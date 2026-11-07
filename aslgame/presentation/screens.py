"""The app's screens. Each handles its own input, update, and draw, and returns an Action to change screen."""

import pygame

from aslgame import config, theme
from aslgame.game import match_detector
from aslgame.game.app_flow import Action
from aslgame.game.match_detector import DetectorState, MatchDetector
from aslgame.game.sign_queue import make_queue, missing_signs
from aslgame.matching import matcher
from aslgame.matching.normalize import normalize, place_at, place_on
from aslgame.presentation.draw import draw_hand, draw_ring, draw_text_centered
from aslgame.presentation.strip import Strip

RING_CENTER_PX = (theme.MARGIN_PX + theme.RING_RADIUS_PX, theme.MARGIN_PX + theme.RING_RADIUS_PX)
CONFIRM_KEYS = (pygame.K_RETURN, pygame.K_SPACE)


def is_key(event, keys):
    return event.type == pygame.KEYDOWN and event.key in keys


def make_shade(size_px):
    shade = pygame.Surface(size_px, pygame.SRCALPHA)
    shade.fill(theme.SHADE)
    return shade


class BootScreen:
    """Shown until the tracker has produced its first result."""

    def handle_event(self, event):
        return None

    def update(self, now_s, result):
        return Action.READY if result is not None else None

    def draw(self, screen, now_s, hand):
        center_px = (screen.get_width() // 2, screen.get_height() // 2)
        draw_ring(screen, center_px, theme.RING_RADIUS_PX, now_s % 1.0, theme.INK)


class MenuScreen:
    def __init__(self, fonts, sign_names, size_px):
        self.words = list(config.LEARN_WORDS)
        self._playable = [not missing_signs(word, sign_names) for word in self.words]
        self.selected = self._playable.index(True) if any(self._playable) else None
        self._shade = make_shade(size_px)
        self._normal = [fonts.medium.render(word, True, theme.INK if ok else theme.INK_DIM)
                        for word, ok in zip(self.words, self._playable)]
        self._selected = [fonts.large.render(word, True, theme.INK) for word in self.words]
        self._missing = [fonts.small.render(" ".join(missing_signs(word, sign_names)), True, theme.INK_DIM)
                         for word in self.words]
        self._hint = fonts.small.render(
            "Enter  start" if self.selected is not None else "Record signs: python -m aslgame.tools.capture A",
            True, theme.INK_DIM)

    def handle_event(self, event):
        if is_key(event, (pygame.K_ESCAPE,)):
            return Action.QUIT
        if self.selected is None:
            return None
        if is_key(event, (pygame.K_UP,)):
            self._step(-1)
        elif is_key(event, (pygame.K_DOWN,)):
            self._step(1)
        elif is_key(event, CONFIRM_KEYS):
            return Action.START_LEARN
        return None

    def _step(self, direction):
        index = self.selected
        for _ in self.words:
            index = (index + direction) % len(self.words)
            if self._playable[index]:
                self.selected = index
                return

    def selected_word(self):
        return self.words[self.selected]

    def update(self, now_s, result):
        return None

    def draw(self, screen, now_s, hand):
        screen.blit(self._shade, (0, 0))
        x_px = screen.get_width() // 3
        top_px = (screen.get_height() - theme.MENU_ROW_PX * len(self.words)) // 2
        for index in range(len(self.words)):
            center_y_px = top_px + theme.MENU_ROW_PX * index + theme.MENU_ROW_PX // 2
            label = self._selected[index] if index == self.selected else self._normal[index]
            screen.blit(label, label.get_rect(midleft=(x_px, center_y_px)))
            if index == self.selected:
                marker = pygame.Rect(0, 0, theme.MENU_MARKER_PX, label.get_height())
                marker.midright = (x_px - theme.GRID_PX * 2, center_y_px)
                pygame.draw.rect(screen, theme.ACCENT, marker)
            if not self._playable[index]:
                missing = self._missing[index]
                screen.blit(missing, missing.get_rect(midleft=(label.get_rect().width + x_px + theme.GRID_PX * 3, center_y_px)))
        draw_text_centered(screen, self._hint, (screen.get_width() // 2, screen.get_height() - theme.MARGIN_PX))


class LearnScreen:
    def __init__(self, fonts, signs, word, size_px):
        self._signs = signs
        self.queue = make_queue(word)
        self._detector = MatchDetector()
        self._score = 0.0
        self._scored_result = None
        self._strip = Strip(fonts.medium, self.queue, size_px)
        self._letters = {name: fonts.large.render(name, True, theme.INK) for name in set(self.queue.text) - {" "}}
        self._idle_wrist = (size_px[0] / 2 + theme.IDLE_GHOST_OFFSET_PX[0], size_px[1] / 2 + theme.IDLE_GHOST_OFFSET_PX[1], 0)
        self._labels = {
            DetectorState.NO_HAND: fonts.medium.render("Show your hand", True, theme.INK),
            DetectorState.SEARCHING: fonts.medium.render("Match the outline", True, theme.INK),
            DetectorState.HOLDING: fonts.medium.render("Hold", True, theme.ACCENT),
            DetectorState.MATCHED: fonts.medium.render("Hold", True, theme.ACCENT),
        }
        self._done_label = fonts.medium.render("Enter", True, theme.INK)

    def handle_event(self, event):
        if is_key(event, (pygame.K_ESCAPE, pygame.K_p)):
            return Action.PAUSE
        if self.queue.is_done() and is_key(event, CONFIRM_KEYS):
            return Action.TO_MENU
        return None

    def update(self, now_s, result):
        if self.queue.is_done():
            return None
        hand = result.hand if result else None
        if result is not self._scored_result:
            # Scoring runs once per tracking result, not once per frame.
            self._scored_result = result
            sign = self._signs[self.queue.current_sign()]
            self._score = matcher.target_score(normalize(hand.points_px, hand.is_left), sign, self._signs) if hand else 0.0
        if match_detector.update(self._detector, now_s, self._score if hand else None):
            self.queue.advance()
            self._detector = MatchDetector()
            self._scored_result = None
        return None

    def draw(self, screen, now_s, hand):
        if hand is not None:
            draw_hand(screen, hand.points_px, theme.LIVE_HAND, theme.LIVE_LINE_PX, theme.LIVE_JOINT_RADIUS_PX, True)
        self._strip.draw(screen)
        label_center_px = (screen.get_width() // 2, self._strip.top_px - theme.GRID_PX * 4)
        if self.queue.is_done():
            draw_text_centered(screen, self._done_label, label_center_px)
            return
        sign = self._signs[self.queue.current_sign()]
        if hand is not None:
            ghost_px = place_on(sign.outline, hand.points_px, hand.is_left)
        else:
            ghost_px = place_at(sign.outline, self._idle_wrist, theme.IDLE_GHOST_PALM_PX, False)
        matched = self._score >= config.MATCH_THRESHOLD and hand is not None
        draw_hand(screen, ghost_px, theme.GHOST, theme.GHOST_LINE_PX, theme.GHOST_JOINT_RADIUS_PX, matched)
        draw_ring(screen, RING_CENTER_PX, theme.RING_RADIUS_PX, 1.0, theme.INK_DIM)
        draw_ring(screen, RING_CENTER_PX, theme.RING_RADIUS_PX, self._detector.hold_fraction, theme.ACCENT)
        draw_text_centered(screen, self._letters[sign.name], RING_CENTER_PX)
        draw_text_centered(screen, self._labels[self._detector.state], label_center_px)


class PausedScreen:
    def __init__(self, fonts, size_px):
        self._shade = make_shade(size_px)
        self._title = fonts.large.render("Paused", True, theme.INK)
        self._hint = fonts.small.render("Space  resume      Esc  menu", True, theme.INK_DIM)

    def handle_event(self, event):
        if is_key(event, (pygame.K_SPACE, pygame.K_p, pygame.K_RETURN)):
            return Action.RESUME
        if is_key(event, (pygame.K_ESCAPE,)):
            return Action.TO_MENU
        return None

    def update(self, now_s, result):
        return None

    def draw(self, screen, now_s, hand):
        screen.blit(self._shade, (0, 0))
        center_px = (screen.get_width() // 2, screen.get_height() // 2)
        draw_text_centered(screen, self._title, center_px)
        draw_text_centered(screen, self._hint, (center_px[0], center_px[1] + theme.GRID_PX * 8))
