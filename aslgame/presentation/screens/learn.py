"""Learn mode: match each sign of a word at your own pace."""

from aslgame import config, theme
from aslgame.game import match_detector
from aslgame.game.app_flow import Action
from aslgame.game.match_detector import DetectorState, MatchDetector
from aslgame.game.sign_queue import make_queue
from aslgame.presentation.draw import draw_text_centered
from aslgame.presentation.screens.common import (
    CONFIRM_KEYS, PAUSE_KEYS, FixHint, Ghost, ReferenceCard, TargetScorer, TopBar, is_key,
)
from aslgame.presentation.strip import Strip
from aslgame.presentation.ui import Button


class LearnScreen:
    def __init__(self, fonts, signs, word, size_px):
        self._signs = signs
        self.queue = make_queue(word)
        self._detector = MatchDetector()
        self._scorer = TargetScorer(signs)
        self._strip = Strip(fonts.medium, self.queue, size_px)
        self._ghost = Ghost(size_px)
        self._card = ReferenceCard(fonts, signs, set(self.queue.text) - {" "})
        self._top_bar = TopBar(size_px)
        self._labels = {
            DetectorState.NO_HAND: fonts.medium.render("Show your hand", True, theme.INK),
            DetectorState.SEARCHING: fonts.medium.render("Match the outline", True, theme.INK),
            DetectorState.HOLDING: fonts.medium.render("Hold it", True, theme.ACCENT),
            DetectorState.MATCHED: fonts.medium.render("Hold it", True, theme.ACCENT),
        }
        self._done_label = fonts.medium.render("Done", True, theme.ACCENT)
        menu_rect = (0, 0, theme.GRID_PX * 24, theme.BUTTON_HEIGHT_PX)
        self._menu_button = Button(fonts.body, "Back to menu", menu_rect, primary=True)
        self._menu_button.rect.center = (size_px[0] // 2, size_px[1] // 2)
        self._fix_hint = FixHint(fonts)

    def handle_event(self, event):
        if is_key(event, PAUSE_KEYS) or self._top_bar.pause_clicked(event):
            return Action.PAUSE
        if self.queue.is_done() and (is_key(event, CONFIRM_KEYS) or self._menu_button.is_clicked(event)):
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
        self._top_bar.draw(screen)
        self._strip.draw(screen)
        title_center_px = (screen.get_width() // 2, theme.TOP_BAR_HEIGHT_PX // 2)
        if self.queue.is_done():
            draw_text_centered(screen, self._done_label, title_center_px)
            self._menu_button.draw(screen, focused=True)
            return
        sign = self._signs[self.queue.current_sign()]
        matched = hand is not None and self._scorer.score >= config.MATCH_THRESHOLD
        fingers_off = self._scorer.fingers_off if hand is not None else []
        self._ghost.draw(screen, sign, hand, matched, fingers_off)
        self._card.draw(screen, sign.name, self._detector.hold_fraction)
        draw_text_centered(screen, self._labels[self._detector.state], title_center_px)
        self._fix_hint.draw(screen, fingers_off)

