"""Rhythm, Music, and Rush: timed play in ink and fire.

Rhythm: a brush ring closes in on your hand; sign before it meets the inner ring.
Music and Rush: a brush-stroke fuse burns down around your hand; sign before it is gone.
"""

import math

import pygame

from aslgame import config, theme
from aslgame.game import rhythm, rush
from aslgame.game.app_flow import Action
from aslgame.game.rhythm import NoteState
from aslgame.game.scoring import EventKind, Judgement
from aslgame.hand import FINGER_BASES, WRIST
from aslgame.matching.normalize import palm_size
from aslgame.presentation import ink
from aslgame.presentation.arcade import ArcadeFx
from aslgame.presentation.draw import draw_text_centered
from aslgame.presentation.screens.common import (
    PAUSE_KEYS, FixHint, Ghost, ReferenceCard, TargetScorer, TopBar, draw_motion, idle_wrist, is_key,
)
from aslgame.presentation.strip import Strip

PALM_POINTS = [WRIST] + FINGER_BASES
SCALE_STEPS = 8  # pitches of the Perfect sound as a combo climbs
FUSE_WARNING = 0.25


class RhythmScreen:
    """clock is anything with time, pause, and resume: a GameClock, or a MediaPlayer in music mode.

    The clock starts after the countdown, so game time is negative while it runs.
    """

    def __init__(self, fonts, signs, queue, session, clock, size_px, settings, sfx, run_length_s):
        self._signs = signs
        self.queue = queue
        self.session = session
        self.rush = isinstance(session, rush.RushSession)
        self.clock = clock
        self._run_length_s = run_length_s
        self._scorer = TargetScorer(signs)
        self._fonts = fonts
        self._strip = Strip(fonts.serif_mode, self.queue, size_px)
        self._ghost = Ghost(size_px, settings)
        self._card = ReferenceCard(fonts, signs, set(session.signs), settings)
        self._top_bar = TopBar(size_px)
        self._fix_hint = FixHint(fonts)
        self._idle_wrist = idle_wrist(size_px)
        count_font = pygame.font.SysFont(theme.SERIF_FAMILIES, 200)
        self._count_labels = [ink.halo_text(count_font, str(n), theme.INK_BLACK, halo_px=5) for n in range(1, config.COUNTDOWN_STEPS + 1)]
        self._go = ink.halo_text(pygame.font.SysFont(theme.SERIF_FAMILIES, 200, italic=True), "Go", theme.SEAL, halo_px=5)
        self._enso = ink.BrushRing(seed=21)
        self._fuse = ink.BrushRing(seed=7)
        self._approach = ink.BrushRing(seed=3)
        self._last_count = None
        self._sfx = sfx
        self._strip_judgements = []
        self._fx = ArcadeFx(fonts, size_px, settings, sfx)
        self._last_draw_s = None
        self._canvas = pygame.Surface(size_px, pygame.SRCALPHA)
        self._clock_font = pygame.font.SysFont(theme.SERIF_FAMILIES, 36)
        self._clock_label = None
        self._clock_value = None

    @property
    def tally(self):
        return self.session.tally

    def camera_grade(self):
        return ink.grade_matrix(self._fx.heat, self._fx.ash)

    def pause(self, now_s):
        self.clock.pause(now_s)

    def resume(self, now_s):
        self.clock.resume(now_s)

    def handle_event(self, event):
        return Action.PAUSE if is_key(event, PAUSE_KEYS) or self._top_bar.pause_clicked(event) else None

    def _target_sign(self):
        if self.rush:
            return self.session.target()
        note = self.session.target()
        return None if note is None else note.sign

    def update(self, now_s, result):
        game_s = self.clock.time(now_s)
        self._update_countdown(game_s)
        if game_s < 0:
            return None
        sign = self._target_sign()
        hand = result.hand if result else None
        score = self._scorer.update(result, sign) if sign is not None and hand is not None else None
        (rush.update if self.rush else rhythm.update)(self.session, game_s, score)
        center, radius = self._hit_ring(hand)
        for event in self.tally.events:
            self._play_sound(event)
            self._fx.event(event, center, radius, now_s)
        self.tally.events.clear()
        self.queue.current = len(self.tally.results)
        while len(self._strip_judgements) < len(self.tally.results):
            self._strip_judgements.append(self.tally.results[len(self._strip_judgements)][1])
        return Action.FINISH if self.session.is_finished() else None

    def _update_countdown(self, game_s):
        step = math.ceil(-game_s / config.COUNTDOWN_STEP_S) if game_s < 0 else 0
        if step != self._last_count:
            self._last_count = step
            self._sfx.play("go" if step == 0 else "tick")

    def _play_sound(self, event):
        if event.kind == EventKind.HIT:
            step = min(SCALE_STEPS - 1, event.combo // config.PITCH_STEP_COMBO)
            self._sfx.play(f"perfect{step}" if event.judgement == Judgement.PERFECT else event.judgement.name.lower())
        elif event.kind == EventKind.MISS:
            self._sfx.play("miss")
        elif event.kind == EventKind.TIER_UP:
            self._sfx.play("tier")
        elif event.kind == EventKind.BREAK:
            self._sfx.play("break")
        elif event.kind == EventKind.WORD:
            self._sfx.play("word")
        elif event.kind == EventKind.LOCK:
            self._sfx.play("lock")

    def draw(self, screen, now_s, hand):
        game_s = self.clock.time(now_s)
        frame_s = 0.0 if self._last_draw_s is None else min(0.1, now_s - self._last_draw_s)
        self._last_draw_s = now_s
        fx = self._fx
        fx.update(now_s, frame_s, self.tally.multiplier)
        fx.draw_backdrop(screen)
        fx.draw_fire_back(screen, now_s)
        # Play is drawn on a canvas so a tier-up can shake it without shaking the camera picture.
        canvas = self._canvas
        canvas.fill((0, 0, 0, 0))
        fx.draw_under(canvas, now_s)
        self._strip.draw(canvas, self._strip_judgements)
        sign_name = self._target_sign()
        center_px, hit_radius_px = self._hit_ring(hand)
        if sign_name is not None:
            sign = self._signs[sign_name]
            matched = hand is not None and self._scorer.shape_ok
            fingers_off = self._scorer.fingers_off if hand is not None else []
            self._ghost.draw(canvas, sign, hand, matched, fingers_off)
            draw_motion(canvas, self._scorer, sign, hand, self._idle_wrist, now_s, True)
            self._fix_hint.draw(canvas, fingers_off)
            if self.rush:
                self._draw_fuse(canvas, game_s, now_s, frame_s, center_px, hit_radius_px)
                self._card.draw(canvas, sign.name, 1.0 - self.session.fuse_fraction(max(0.0, game_s)))
            else:
                note = self.session.target()
                self._card.draw(canvas, sign.name, 1.0 - note.approach_fraction(game_s))
                if note.state != NoteState.WAITING:
                    self._draw_approach(canvas, note, game_s, center_px, hit_radius_px)
        self._draw_locked(canvas, center_px, hit_radius_px)
        fx.draw_over(canvas, now_s)
        screen.blit(canvas, fx.shake_offset(now_s))
        self._top_bar.draw(screen)
        if not self.rush or self.session.bpm:
            self._draw_beat(screen, game_s)
        self._draw_clock(screen, game_s)
        fx.draw_hud(screen, self.tally.score, self.tally.multiplier, self._top_bar.pause_rect.left - theme.GRID_PX * 3, now_s)
        fx.draw_fire_front(screen, now_s)
        if game_s < config.COUNTDOWN_STEP_S * 0.5:
            self._draw_countdown(screen, game_s)

    def _ring_width(self, radius_px):
        return max(10.0, min(26.0, radius_px * 0.13))

    def _draw_fuse(self, canvas, game_s, now_s, frame_s, center_px, radius_px):
        """The fuse: a brush stroke that burns down from its end. Near the end it swells, so the warning is in its shape too."""
        fuse = self.session.fuse_fraction(max(0.0, game_s))
        ring_px = radius_px
        if self.session.bpm and game_s >= 0:
            # It breathes with the beat, so the music shows on the hand.
            ring_px *= 1.0 + 0.06 * (1.0 - self.session.beat_phase(game_s)) ** 3
        width = self._ring_width(radius_px)
        if fuse < FUSE_WARNING:
            width *= 1.0 + 0.35 * abs(math.sin(now_s * 10))
        self._fuse.draw(canvas, center_px, ring_px, fuse, width, ink.heat_color(self._fx.heat))
        if game_s >= 0 and fuse > 0.01:
            tip = ink.BrushRing.point(center_px, ring_px, fuse)
            self._fx.burn_fuse(tip, center_px, ring_px, fuse, now_s, frame_s)

    def _draw_approach(self, canvas, note, game_s, center_px, hit_radius_px):
        """Rhythm: a thin inked target ring, and a brush ring closing in on it."""
        hittable = note.state == NoteState.HITTABLE
        pygame.draw.circle(canvas, theme.PAPER, center_px, hit_radius_px, theme.HIT_RING_LINE_PX + 4)
        pygame.draw.circle(canvas, theme.SEAL if hittable else theme.INK_BLACK, center_px, hit_radius_px, theme.HIT_RING_LINE_PX)
        scale = 1.0 + (theme.APPROACH_RING_START_SCALE - 1.0) * note.approach_fraction(game_s)
        self._approach.draw(canvas, center_px, hit_radius_px * scale, 1.0, self._ring_width(hit_radius_px) * 0.7, ink.heat_color(self._fx.heat))

    def _draw_locked(self, canvas, center_px, hit_radius_px):
        """Rhythm: signs made ahead of their beat wait as ink dots on the ring until it lands."""
        if self.rush:
            return
        locked = [n for n in self.session.notes if n.locked_s is not None and n.judgement is None]
        for index, _ in enumerate(locked):
            angle = -math.pi / 2 + (index + 1) * 0.5
            at = (center_px[0] + math.cos(angle) * hit_radius_px, center_px[1] + math.sin(angle) * hit_radius_px)
            pygame.draw.circle(canvas, theme.PAPER, at, theme.GRID_PX * 1.5 + 3)
            pygame.draw.circle(canvas, ink.heat_color(self._fx.heat), at, theme.GRID_PX * 1.5)

    def _draw_countdown(self, screen, game_s):
        """3, 2, 1, Go: each number inside an ink circle that paints itself in."""
        center = (screen.get_width() // 2, screen.get_height() // 2 - theme.GRID_PX * 4)
        if game_s >= 0:
            surface, age = self._go, game_s / (config.COUNTDOWN_STEP_S * 0.5)
        else:
            step = math.ceil(-game_s / config.COUNTDOWN_STEP_S)
            surface = self._count_labels[min(step, len(self._count_labels)) - 1]
            age = 1.0 - ((-game_s) % config.COUNTDOWN_STEP_S) / config.COUNTDOWN_STEP_S
        self._enso.draw(screen, center, theme.GRID_PX * 17, min(1.0, age * 1.6), theme.GRID_PX * 3, theme.INK_BLACK)
        shown = pygame.transform.smoothscale_by(surface, 1.3 - 0.3 * min(1.0, age * 4))
        shown.set_alpha(int(255 * (1 - max(0.0, age - 0.7) / 0.3)))
        draw_text_centered(screen, shown, center)

    def _draw_clock(self, screen, game_s):
        """Time left in the run, in ink at the left of the band."""
        if self.rush:
            left_s = self.session.time_left_s(max(0.0, game_s)) if game_s >= 0 else self.session.length_s
        else:
            left_s = max(0.0, self._run_length_s - max(0.0, game_s))
        value = math.ceil(left_s)
        if value != self._clock_value:
            self._clock_value = value
            color = theme.SEAL if value <= 5 else theme.INK_BLACK
            self._clock_label = self._clock_font.render(f"{value // 60}:{value % 60:02d}", True, color)
        screen.blit(self._clock_label, self._clock_label.get_rect(midleft=(theme.MARGIN_PX, theme.TOP_BAR_HEIGHT_PX // 2 - 4)))

    def _hit_ring(self, hand):
        """The ring sits around the palm, so the cue is where the player is looking."""
        if hand is None:
            wrist = self._idle_wrist
            return (wrist[0], wrist[1] - theme.IDLE_GHOST_PALM_PX), theme.IDLE_GHOST_PALM_PX * theme.HIT_RING_PALM_SCALE
        center = hand.points_px[PALM_POINTS, :2].mean(axis=0)
        return tuple(center.tolist()), palm_size(hand.points_px) * theme.HIT_RING_PALM_SCALE

    def _draw_beat(self, screen, game_s):
        """A vermilion seal dot that swells on each beat."""
        pulse = (1.0 - self.session.beat_phase(max(0.0, game_s))) ** 2 if game_s >= 0 else 0.0
        radius_px = theme.BEAT_DOT_RADIUS_PX + theme.BEAT_PULSE_PX * pulse
        pygame.draw.circle(screen, theme.SEAL, (screen.get_width() // 2, theme.TOP_BAR_HEIGHT_PX // 2 - 4), radius_px)
