"""Rhythm and music modes: signs arrive on a beat. A ring closes in on your hand; sign when it meets the inner ring."""

import pygame

from aslgame import config, theme
from aslgame.game import rhythm
from aslgame.game.app_flow import Action
from aslgame.game.rhythm import Judgement, NoteState
from aslgame.hand import FINGER_BASES, WRIST
from aslgame.matching.normalize import palm_size
from aslgame.presentation.draw import draw_text_centered
from aslgame.presentation.screens.common import (
    JUDGEMENT_TEXT, PAUSE_KEYS, FixHint, Ghost, ReferenceCard, TargetScorer, TopBar, idle_wrist, is_key,
)
from aslgame.presentation.strip import Strip

OPEN_STATES = (NoteState.WAITING, NoteState.APPROACHING, NoteState.HITTABLE)
PALM_POINTS = [WRIST] + FINGER_BASES


class RhythmScreen:
    """clock is anything with time, pause, and resume: a GameClock, or a MediaPlayer in music mode."""

    def __init__(self, fonts, signs, queue, session, clock, size_px):
        self._signs = signs
        self.queue = queue
        self.session = session
        self.clock = clock
        self._scorer = TargetScorer(signs)
        self._fonts = fonts
        self._strip = Strip(fonts.medium, self.queue, size_px)
        self._ghost = Ghost(size_px)
        self._card = ReferenceCard(fonts, signs, set(session.signs))
        self._top_bar = TopBar(size_px)
        self._fix_hint = FixHint(fonts)
        self._idle_wrist = idle_wrist(size_px)
        self._judgements = {j: fonts.medium.render(text, True, theme.ACCENT if j != Judgement.MISS else theme.FINGER_FIX)
                            for j, text in JUDGEMENT_TEXT.items()}
        self._hud_values = None
        self._hud = []

    def pause(self, now_s):
        self.clock.pause(now_s)

    def resume(self, now_s):
        self.clock.resume(now_s)

    def handle_event(self, event):
        return Action.PAUSE if is_key(event, PAUSE_KEYS) or self._top_bar.pause_clicked(event) else None

    def update(self, now_s, result):
        game_s = self.clock.time(now_s)
        target = self.session.target()
        hand = result.hand if result else None
        score = self._scorer.update(result, target.sign) if target is not None and hand is not None else None
        rhythm.update(self.session, game_s, score)
        self.queue.current = len(self.session.results)
        return Action.FINISH if self.session.is_finished() else None

    def draw(self, screen, now_s, hand):
        game_s = self.clock.time(now_s)
        self._top_bar.draw(screen)
        self._strip.draw(screen)
        target = self.session.target()
        center_px, hit_radius_px = self._hit_ring(hand)
        if target is not None:
            sign = self._signs[target.sign]
            matched = hand is not None and self._scorer.score >= config.MATCH_THRESHOLD
            fingers_off = self._scorer.fingers_off if hand is not None else []
            self._ghost.draw(screen, sign, hand, matched, fingers_off)
            self._card.draw(screen, sign.name, 1.0 - target.approach_fraction(game_s))
            self._fix_hint.draw(screen, fingers_off)
            if target.state != NoteState.WAITING:
                self._draw_approach(screen, target, game_s, center_px, hit_radius_px)
        self._draw_feedback(screen, game_s, center_px, hit_radius_px)
        self._draw_beat(screen, game_s)
        self._draw_hud(screen)

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

    def _draw_feedback(self, screen, game_s, center_px, hit_radius_px):
        for note in self.session.notes:
            if note.state in OPEN_STATES or note.judgement is None:
                continue
            age = min(1.0, (game_s - note.resolved_s) / config.FEEDBACK_S)
            y_px = center_px[1] - hit_radius_px - theme.GRID_PX * 2 - theme.JUDGEMENT_RISE_PX * age
            draw_text_centered(screen, self._judgements[note.judgement], (center_px[0], y_px))
            if note.judgement != Judgement.MISS:
                pygame.draw.circle(screen, theme.ACCENT, center_px, hit_radius_px * (1.0 + theme.HIT_FLASH_GROWTH * age),
                                   theme.APPROACH_RING_LINE_PX)

    def _draw_beat(self, screen, game_s):
        pulse = (1.0 - self.session.beat_phase(game_s)) ** 2
        radius_px = theme.BEAT_DOT_RADIUS_PX + theme.BEAT_PULSE_PX * pulse
        pygame.draw.circle(screen, theme.ACCENT, (screen.get_width() // 2, theme.TOP_BAR_HEIGHT_PX // 2), radius_px)

    def _draw_hud(self, screen):
        values = (self.session.score, self.session.combo)
        if values != self._hud_values:
            # Re-rendered only when a value changes.
            self._hud_values = values
            self._hud = [
                self._fonts.medium.render(str(values[0]), True, theme.INK),
                self._fonts.body.render(f"x{values[1]}", True, theme.ACCENT if values[1] else theme.INK_DIM),
            ]
        right_px = self._top_bar.pause_rect.left - theme.GRID_PX * 3
        center_y_px = theme.TOP_BAR_HEIGHT_PX // 2
        for surface in reversed(self._hud):
            rect = screen.blit(surface, surface.get_rect(midright=(right_px, center_y_px)))
            right_px = rect.left - theme.GRID_PX * 2
