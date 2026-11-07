"""Learn mode: match each sign of a word at your own pace."""

from aslgame import config, theme
from aslgame.game import match_detector
from aslgame.game.app_flow import Action
from aslgame.game.match_detector import DetectorState, MatchDetector
from aslgame.game.sign_queue import make_queue
from aslgame.presentation.draw import draw_ring, draw_text_centered
from aslgame.presentation.screens.common import (
    CONFIRM_KEYS, PAUSE_KEYS, RING_CENTER_PX, TargetScorer, draw_ghost, draw_live_hand, ghost_points, idle_wrist, is_key,
)
from aslgame.presentation.strip import Strip


class LearnScreen:
    def __init__(self, fonts, signs, word, size_px):
        self._signs = signs
        self.queue = make_queue(word)
        self._detector = MatchDetector()
        self._scorer = TargetScorer(signs)
        self._strip = Strip(fonts.medium, self.queue, size_px)
        self._letters = {name: fonts.large.render(name, True, theme.INK) for name in set(self.queue.text) - {" "}}
        self._idle_wrist = idle_wrist(size_px)
        self._labels = {
            DetectorState.NO_HAND: fonts.medium.render("Show your hand", True, theme.INK),
            DetectorState.SEARCHING: fonts.medium.render("Match the outline", True, theme.INK),
            DetectorState.HOLDING: fonts.medium.render("Hold", True, theme.ACCENT),
            DetectorState.MATCHED: fonts.medium.render("Hold", True, theme.ACCENT),
        }
        self._done_label = fonts.medium.render("Enter", True, theme.INK)

    def handle_event(self, event):
        if is_key(event, PAUSE_KEYS):
            return Action.PAUSE
        if self.queue.is_done() and is_key(event, CONFIRM_KEYS):
            return Action.TO_MENU
        return None

    def update(self, now_s, result):
        if self.queue.is_done():
            return None
        hand = result.hand if result else None
        score = self._scorer.update(result, self.queue.current_sign())
        if match_detector.update(self._detector, now_s, score if hand else None):
            self.queue.advance()
            self._detector = MatchDetector()
        return None

    def draw(self, screen, now_s, hand):
        draw_live_hand(screen, hand)
        self._strip.draw(screen)
        label_center_px = (screen.get_width() // 2, self._strip.top_px - theme.GRID_PX * 4)
        if self.queue.is_done():
            draw_text_centered(screen, self._done_label, label_center_px)
            return
        sign = self._signs[self.queue.current_sign()]
        matched = hand is not None and self._scorer.score >= config.MATCH_THRESHOLD
        draw_ghost(screen, ghost_points(sign, hand, self._idle_wrist), matched)
        draw_ring(screen, RING_CENTER_PX, theme.RING_RADIUS_PX, 1.0, theme.INK_DIM)
        draw_ring(screen, RING_CENTER_PX, theme.RING_RADIUS_PX, self._detector.hold_fraction, theme.ACCENT)
        draw_text_centered(screen, self._letters[sign.name], RING_CENTER_PX)
        draw_text_centered(screen, self._labels[self._detector.state], label_center_px)
