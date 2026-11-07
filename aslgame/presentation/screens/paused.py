"""Pause overlay for any mode."""

import pygame

from aslgame import theme
from aslgame.game.app_flow import Action
from aslgame.presentation.draw import draw_text_centered
from aslgame.presentation.screens.common import is_key, make_shade


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
