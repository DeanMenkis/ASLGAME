"""Learn and Recall modes: match each sign of a word at your own pace.

Recall hides the shape and shows only the letter; Tab or the Hint button shows it again.
"""

import pygame

from aslgame import theme
from aslgame.game import match_detector
from aslgame.game.app_flow import Action
from aslgame.game.match_detector import DetectorState, MatchDetector
from aslgame.game.scoring import Judgement
from aslgame.game.sign_queue import make_queue
from aslgame.presentation.draw import draw_text_centered
from aslgame.presentation.screens.common import (
    CONFIRM_KEYS, PAUSE_KEYS, FixHint, Ghost, ReferenceCard, TargetScorer, TopBar, draw_motion, idle_wrist, is_key,
)
from aslgame.game.motion import MOTION_SIGNS, MotionState
from aslgame.presentation.strip import Strip
from aslgame.presentation.ui import Button

# Recall reuses the judgement look in the strip: from memory reads as best, with a hint as lowest pass.
FROM_MEMORY = Judgement.PERFECT
WITH_HINT = Judgement.OK


class LearnScreen:
    def __init__(self, fonts, signs, word, size_px, settings, sfx, recall=False):
        self._signs = signs
        self._fonts = fonts
        self.recall = recall
        self.queue = make_queue(word)
        self._detector = MatchDetector()
        self._scorer = TargetScorer(signs)
        self._strip = Strip(fonts.medium, self.queue, size_px)
        self._ghost = Ghost(size_px, settings)
        self._card = ReferenceCard(fonts, signs, set(self.queue.text) - {" "}, settings)
        self._top_bar = TopBar(size_px)
        self._fix_hint = FixHint(fonts)
        self._sfx = sfx
        self._hint_on = False
        self._hinted = False
        self.outcomes = []  # FROM_MEMORY or WITH_HINT per finished sign, in recall mode
        searching = "Sign it from memory" if recall else "Match the outline"
        self._labels = {
            DetectorState.NO_HAND: fonts.medium.render("Show your hand", True, theme.INK),
            DetectorState.SEARCHING: fonts.medium.render(searching, True, theme.INK),
            DetectorState.HOLDING: fonts.medium.render("Hold it", True, theme.ACCENT),
            DetectorState.MATCHED: fonts.medium.render("Hold it", True, theme.ACCENT),
        }
        self._draw_labels = {name: fonts.medium.render(f"Draw the {name}", True, theme.ACCENT) for name in MOTION_SIGNS}
        self._idle_wrist = idle_wrist(size_px)
        self._done_label = fonts.medium.render("Done", True, theme.ACCENT)
        self._done_detail = None
        menu_rect = (0, 0, theme.GRID_PX * 24, theme.BUTTON_HEIGHT_PX)
        self._menu_button = Button(fonts.body, "Back to menu", menu_rect, primary=True)
        self._menu_button.rect.center = (size_px[0] // 2, size_px[1] // 2)
        hint_rect = pygame.Rect(0, 0, theme.HINT_BUTTON_WIDTH_PX, theme.ICON_BUTTON_PX)
        hint_rect.midright = (self._top_bar.pause_rect.left - theme.GRID_PX * 2, self._top_bar.pause_rect.centery)
        self._hint_button = Button(fonts.small, "Hint  Tab", hint_rect)

    def handle_event(self, event):
        if is_key(event, PAUSE_KEYS) or self._top_bar.pause_clicked(event):
            return Action.PAUSE
        if self.queue.is_done():
            if is_key(event, CONFIRM_KEYS) or self._menu_button.is_clicked(event):
                return Action.TO_MENU
            return None
        if self.recall and (is_key(event, (pygame.K_TAB,)) or self._hint_button.is_clicked(event)):
            self._hint_on = not self._hint_on
            self._hinted = self._hinted or self._hint_on
        return None

    def update(self, now_s, result):
        if self.queue.is_done():
            return None
        hand = result.hand if result else None
        score = self._scorer.update(result, self.queue.current_sign())
        if match_detector.update(self._detector, now_s, score if hand else None):
            self._finish_sign()
        return None

    def _finish_sign(self):
        self.outcomes.append(WITH_HINT if self._hinted else FROM_MEMORY)
        self.queue.advance()
        self._detector = MatchDetector()
        self._hint_on = self._hinted = False
        self._sfx.play("complete" if self.queue.is_done() else "confirm")
        if self.queue.is_done() and self.recall:
            remembered = self.outcomes.count(FROM_MEMORY)
            text = f"{remembered} of {len(self.outcomes)} from memory"
            self._done_detail = self._fonts.body.render(text, True, theme.INK)

    def _shows_shape(self):
        return not self.recall or self._hint_on

    def draw(self, screen, now_s, hand):
        self._top_bar.draw(screen)
        self._strip.draw(screen, self.outcomes if self.recall else None)
        title_center_px = (screen.get_width() // 2, theme.TOP_BAR_HEIGHT_PX // 2)
        if self.queue.is_done():
            draw_text_centered(screen, self._done_label, title_center_px)
            if self._done_detail is not None:
                draw_text_centered(screen, self._done_detail, (screen.get_width() // 2, self._menu_button.rect.top - theme.GRID_PX * 5))
            self._menu_button.draw(screen, focused=True)
            return
        sign = self._signs[self.queue.current_sign()]
        shows_shape = self._shows_shape()
        if shows_shape:
            matched = hand is not None and self._scorer.shape_ok
            fingers_off = self._scorer.fingers_off if hand is not None else []
            self._ghost.draw(screen, sign, hand, matched, fingers_off)
            self._fix_hint.draw(screen, fingers_off)
        draw_motion(screen, self._scorer, sign, hand, self._idle_wrist, now_s, shows_shape)
        self._card.draw(screen, sign.name, self._detector.hold_fraction, letter_only=not shows_shape)
        if self.recall:
            self._hint_button.draw(screen, focused=self._hint_on)
        draw_text_centered(screen, self._title(sign.name), title_center_px)

    def _title(self, name):
        tracker = self._scorer.tracker
        if tracker is not None and tracker.state == MotionState.DRAWING:
            return self._draw_labels[name]
        return self._labels[self._detector.state]
