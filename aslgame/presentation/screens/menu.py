"""Menu: pick a mode with Left and Right, a word with Up and Down."""

import pygame

from aslgame import config, theme
from aslgame.game.app_flow import Action
from aslgame.game.sign_queue import missing_signs
from aslgame.presentation.draw import draw_text_centered
from aslgame.presentation.screens.common import CONFIRM_KEYS, is_key, make_shade

MODES = (("Learn", Action.START_LEARN), ("Rhythm", Action.START_RHYTHM))


class MenuScreen:
    def __init__(self, fonts, sign_names, size_px):
        self.words = list(config.LEARN_WORDS)
        self._playable = [not missing_signs(word, sign_names) for word in self.words]
        self.selected = self._playable.index(True) if any(self._playable) else None
        self.mode = 0
        self._shade = make_shade(size_px)
        self._normal = [fonts.medium.render(word, True, theme.INK if ok else theme.INK_DIM)
                        for word, ok in zip(self.words, self._playable)]
        self._selected = [fonts.large.render(word, True, theme.INK) for word in self.words]
        self._missing = [fonts.small.render(" ".join(missing_signs(word, sign_names)), True, theme.INK_DIM)
                         for word in self.words]
        self._modes = [(fonts.medium.render(name, True, theme.INK), fonts.medium.render(name, True, theme.INK_DIM))
                       for name, _ in MODES]
        self._hint = fonts.small.render(
            "Enter  start" if self.selected is not None else "Record signs: python -m aslgame.tools.capture A",
            True, theme.INK_DIM)

    def handle_event(self, event):
        if is_key(event, (pygame.K_ESCAPE,)):
            return Action.QUIT
        if is_key(event, (pygame.K_LEFT,)):
            self.mode = (self.mode - 1) % len(MODES)
        elif is_key(event, (pygame.K_RIGHT,)):
            self.mode = (self.mode + 1) % len(MODES)
        if self.selected is None:
            return None
        if is_key(event, (pygame.K_UP,)):
            self._step(-1)
        elif is_key(event, (pygame.K_DOWN,)):
            self._step(1)
        elif is_key(event, CONFIRM_KEYS):
            return MODES[self.mode][1]
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
        self._draw_modes(screen)
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
                screen.blit(missing, missing.get_rect(midleft=(x_px + label.get_width() + theme.GRID_PX * 3, center_y_px)))
        draw_text_centered(screen, self._hint, (screen.get_width() // 2, screen.get_height() - theme.MARGIN_PX))

    def _draw_modes(self, screen):
        x_px = screen.get_width() // 3
        y_px = theme.MARGIN_PX
        for index, (active, inactive) in enumerate(self._modes):
            label = active if index == self.mode else inactive
            rect = screen.blit(label, (x_px, y_px))
            if index == self.mode:
                underline = pygame.Rect(rect.left, rect.bottom + theme.GRID_PX, rect.width, theme.MENU_MARKER_PX)
                pygame.draw.rect(screen, theme.ACCENT, underline)
            x_px = rect.right + theme.GRID_PX * 6
