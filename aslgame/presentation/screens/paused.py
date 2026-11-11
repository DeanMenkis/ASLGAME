"""Pause overlay for any mode, with buttons and the keys panel."""

import pygame

from aslgame import theme
from aslgame.game.app_flow import Action
from aslgame.presentation.draw import draw_text_centered
from aslgame.presentation.screens.common import is_key, make_shade
from aslgame.presentation.screens.help import HelpPanel
from aslgame.presentation.press import sticker
from aslgame.presentation.ui import stack_buttons

CARD_SIZE_PX = (theme.GRID_PX * 44, theme.GRID_PX * 43)
BUTTON_WIDTH_PX = theme.GRID_PX * 30


class PausedScreen:
    def __init__(self, fonts, size_px):
        self._shade = make_shade(size_px)
        self._card = sticker(CARD_SIZE_PX)
        self._card_rect = self._card.get_rect(center=(size_px[0] // 2, size_px[1] // 2))
        self._title = fonts.large.render("Paused", True, theme.BLUE)
        top_px = self._card_rect.top + theme.GRID_PX * 14
        self._buttons = stack_buttons(fonts.body, ["Resume", "Keys", "Menu"], self._card_rect.centerx, top_px, BUTTON_WIDTH_PX)
        self._actions = [Action.RESUME, None, Action.TO_MENU]
        self._focus = 0
        self._help = HelpPanel(fonts, size_px)

    def handle_event(self, event):
        if self._help.handle_event(event):
            return None
        if is_key(event, (pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_p)):
            return Action.RESUME
        if is_key(event, (pygame.K_m,)):
            return Action.TO_MENU
        if is_key(event, (pygame.K_h,)):
            self._help.visible = True
        elif is_key(event, (pygame.K_UP,)):
            self._focus = (self._focus - 1) % len(self._buttons)
        elif is_key(event, (pygame.K_DOWN,)):
            self._focus = (self._focus + 1) % len(self._buttons)
        elif is_key(event, (pygame.K_RETURN,)):
            return self._press(self._focus)
        for index, button in enumerate(self._buttons):
            if button.is_clicked(event):
                return self._press(index)
        return None

    def _press(self, index):
        if self._actions[index] is None:
            self._help.visible = True
        return self._actions[index]

    def update(self, now_s, result):
        return None

    def draw(self, screen, now_s, hand):
        screen.blit(self._shade, (0, 0))
        screen.blit(self._card, self._card_rect)
        draw_text_centered(screen, self._title, (self._card_rect.centerx, self._card_rect.top + theme.GRID_PX * 7))
        for index, button in enumerate(self._buttons):
            button.draw(screen, focused=index == self._focus)
        self._help.draw(screen)
