"""Rhythm, Music, and Rush: timed play. A ring closes in on your hand; sign before it meets the inner ring.

Rush has no ring: a fuse burns around the hand and the run clock counts down.
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
from aslgame.presentation.arcade import ArcadeFx
from aslgame.presentation.draw import draw_ring, draw_text_centered
from aslgame.presentation.screens.common import (
    JUDGEMENT_TEXT, PAUSE_KEYS, FixHint, Ghost, ReferenceCard, TargetScorer, TopBar, draw_motion, idle_wrist, is_key,
)
from aslgame.presentation.strip import Strip

PALM_POINTS = [WRIST] + FINGER_BASES
SCALE_STEPS = 8  # pitches of the hit sound as a combo climbs


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
        self._strip = Strip(fonts.medium, self.queue, size_px)
        self._ghost = Ghost(size_px, settings)
        self._card = ReferenceCard(fonts, signs, set(session.signs), settings)
        self._top_bar = TopBar(size_px)
        self._fix_hint = FixHint(fonts)
        self._idle_wrist = idle_wrist(size_px)
        self._judgements = {j: fonts.medium.render(text, True, theme.JUDGEMENT_COLORS[j.name]) for j, text in JUDGEMENT_TEXT.items()}
        self._count_labels = [fonts.display.render(str(n), True, theme.INK) for n in range(1, config.COUNTDOWN_STEPS + 1)]
        self._go = fonts.display.render("GO", True, theme.ACCENT)
        self._last_count = None
        self._sfx = sfx
        self._strip_judgements = []
        self._fx = ArcadeFx(fonts, size_px)
        self._last_draw_s = None
        self._feedback = []  # (judgement, game_s) of recent results, for the label over the hand
        self._canvas = pygame.Surface(size_px, pygame.SRCALPHA)
        self._clock_font = fonts.medium
        self._clock_label = None
        self._clock_value = None

    @property
    def tally(self):
        return self.session.tally

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
            if event.kind in (EventKind.HIT, EventKind.MISS):
                self._feedback.append((event.judgement, game_s))
        self.tally.events.clear()
        self._feedback = [f for f in self._feedback if game_s - f[1] < config.FEEDBACK_S]
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
            self._sfx.play(f"{event.judgement.name.lower()}{step}" if event.judgement == Judgement.PERFECT else event.judgement.name.lower())
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
        frame_s = 0.0 if self._last_draw_s is None else now_s - self._last_draw_s
        self._last_draw_s = now_s
        self._fx.update(now_s, frame_s, self.tally.multiplier)
        # Play is drawn on a canvas so a tier-up can shake it without shaking the camera picture.
        canvas = self._canvas
        canvas.fill((0, 0, 0, 0))
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
                fuse = self.session.fuse_fraction(max(0.0, game_s))
                self._card.draw(canvas, sign.name, 1.0 - fuse)
                draw_ring(canvas, (int(center_px[0]), int(center_px[1])), hit_radius_px, fuse, fuse_color(fuse))
            else:
                note = self.session.target()
                self._card.draw(canvas, sign.name, 1.0 - note.approach_fraction(game_s))
                if note.state != NoteState.WAITING:
                    self._draw_approach(canvas, note, game_s, center_px, hit_radius_px)
        self._draw_locked(canvas, game_s, center_px, hit_radius_px)
        self._draw_feedback(canvas, game_s, center_px, hit_radius_px)
        self._fx.draw(canvas, now_s)
        screen.blit(canvas, self._fx.shake_offset(now_s))
        self._top_bar.draw(screen)
        if not self.rush:
            self._draw_beat(screen, game_s)
        self._draw_clock(screen, game_s)
        right_px = self._top_bar.pause_rect.left - theme.GRID_PX * 3
        self._fx.draw_hud(screen, self.tally.score, self.tally.multiplier, right_px, now_s)
        if game_s < 0 or game_s < config.COUNTDOWN_STEP_S * 0.5:
            self._draw_countdown(screen, game_s)

    def _draw_countdown(self, screen, game_s):
        center = (screen.get_width() // 2, screen.get_height() // 2 - theme.GRID_PX * 4)
        if game_s >= 0:
            surface, age = self._go, game_s / (config.COUNTDOWN_STEP_S * 0.5)
        else:
            step = math.ceil(-game_s / config.COUNTDOWN_STEP_S)
            surface = self._count_labels[min(step, len(self._count_labels)) - 1]
            age = 1.0 - ((-game_s) % config.COUNTDOWN_STEP_S) / config.COUNTDOWN_STEP_S
        shown = pygame.transform.smoothscale_by(surface, 1.6 - 0.6 * min(1.0, age * 3))
        shown.set_alpha(int(255 * (1 - age ** 2)))
        draw_ring(screen, center, theme.GRID_PX * 14, 1.0 - age, theme.ACCENT)
        draw_text_centered(screen, shown, center)

    def _draw_clock(self, screen, game_s):
        """Time left in the run, left of the beat dot."""
        if self.rush:
            left_s = self.session.time_left_s(max(0.0, game_s)) if game_s >= 0 else self.session.length_s
        else:
            left_s = max(0.0, self._run_length_s - max(0.0, game_s))
        value = math.ceil(left_s)
        if value != self._clock_value:
            self._clock_value = value
            color = theme.JUDGEMENT_COLORS["MISS"] if value <= 5 else theme.INK
            self._clock_label = self._clock_font.render(f"{value // 60}:{value % 60:02d}", True, color)
        screen.blit(self._clock_label, self._clock_label.get_rect(midleft=(theme.MARGIN_PX, theme.TOP_BAR_HEIGHT_PX // 2)))

    def _hit_ring(self, hand):
        """The inner ring sits around the palm, so the cue is where the player is looking."""
        if hand is None:
            wrist = self._idle_wrist
            return (wrist[0], wrist[1] - theme.IDLE_GHOST_PALM_PX), theme.IDLE_GHOST_PALM_PX * theme.HIT_RING_PALM_SCALE
        center = hand.points_px[PALM_POINTS, :2].mean(axis=0)
        return tuple(center.tolist()), palm_size(hand.points_px) * theme.HIT_RING_PALM_SCALE

    def _draw_approach(self, screen, note, game_s, center_px, hit_radius_px):
        hittable = note.state == NoteState.HITTABLE
        pygame.draw.circle(screen, theme.GHOST_EDGE_DARK, center_px, hit_radius_px, theme.HIT_RING_LINE_PX + 4)
        pygame.draw.circle(screen, theme.INK if hittable else theme.INK_DIM, center_px, hit_radius_px, theme.HIT_RING_LINE_PX)
        scale = 1.0 + (theme.APPROACH_RING_START_SCALE - 1.0) * note.approach_fraction(game_s)
        pygame.draw.circle(screen, theme.ACCENT, center_px, hit_radius_px * scale, theme.APPROACH_RING_LINE_PX)

    def _draw_locked(self, screen, game_s, center_px, hit_radius_px):
        """Signs made ahead of their beat wait as small filled marks that land with it."""
        if self.rush:
            return
        locked = [n for n in self.session.notes if n.locked_s is not None and n.judgement is None]
        for index, note in enumerate(locked):
            angle = -math.pi / 2 + (index + 1) * 0.5
            x_px = center_px[0] + math.cos(angle) * hit_radius_px
            y_px = center_px[1] + math.sin(angle) * hit_radius_px
            pygame.draw.circle(screen, theme.ACCENT, (x_px, y_px), theme.GRID_PX * 1.5)

    def _draw_feedback(self, screen, game_s, center_px, hit_radius_px):
        for judgement, born_s in self._feedback:
            age = min(1.0, (game_s - born_s) / config.FEEDBACK_S)
            y_px = center_px[1] - hit_radius_px - theme.GRID_PX * 2 - theme.JUDGEMENT_RISE_PX * age
            draw_text_centered(screen, self._judgements[judgement], (center_px[0], y_px))

    def _draw_beat(self, screen, game_s):
        pulse = (1.0 - self.session.beat_phase(max(0.0, game_s))) ** 2 if game_s >= 0 else 0.0
        radius_px = theme.BEAT_DOT_RADIUS_PX + theme.BEAT_PULSE_PX * pulse
        pygame.draw.circle(screen, theme.ACCENT, (screen.get_width() // 2, theme.TOP_BAR_HEIGHT_PX // 2), radius_px)


def fuse_color(fraction):
    if fraction > 0.5:
        return theme.JUDGEMENT_COLORS["PERFECT"]
    if fraction > 0.25:
        return theme.JUDGEMENT_COLORS["GOOD"]
    return theme.JUDGEMENT_COLORS["MISS"]
