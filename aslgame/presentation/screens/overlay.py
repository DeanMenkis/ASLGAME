"""A card shown over a screen until a key or click closes it. Drawn once when built."""

import pygame

from aslgame import theme
from aslgame.presentation.ui import make_panel

CLOSE_KEYS = (pygame.K_ESCAPE, pygame.K_h, pygame.K_RETURN, pygame.K_SPACE)


class Overlay:
    def __init__(self, panel, size_px):
        self.visible = False
        self._shade = make_panel(size_px, theme.SHADE, 0)
        self._panel = panel
        self._rect = panel.get_rect(center=(size_px[0] // 2, size_px[1] // 2))

    def handle_event(self, event):
        """Close on a key or a click anywhere. Returns True when the event was used."""
        if not self.visible:
            return False
        if (event.type == pygame.KEYDOWN and event.key in CLOSE_KEYS) or event.type == pygame.MOUSEBUTTONDOWN:
            self.visible = False
        return event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN)

    def draw(self, screen):
        if self.visible:
            screen.blit(self._shade, (0, 0))
            screen.blit(self._panel, self._rect)
