"""Tells the player to add light when the camera picture stays too dark to track a hand well."""

import math

import pygame

from aslgame import config, theme
from aslgame.presentation.ui import make_panel

SUN_RAYS = 8


class LightWarning:
    def __init__(self, fonts, size_px):
        label = fonts.body.render("More light", True, theme.INK)
        icon_px = theme.GRID_PX * 4
        width_px = icon_px + theme.GRID_PX * 3 + label.get_width() + theme.GRID_PX * 4
        self._panel = make_panel((width_px, theme.BUTTON_HEIGHT_PX), theme.SURFACE)
        center = (theme.GRID_PX * 2 + icon_px // 2, theme.BUTTON_HEIGHT_PX // 2)
        draw_sun(self._panel, center, icon_px // 2)
        self._panel.blit(label, label.get_rect(midleft=(center[0] + icon_px // 2 + theme.GRID_PX * 2, center[1])))
        self._rect = self._panel.get_rect(midtop=(size_px[0] // 2, theme.TOP_BAR_HEIGHT_PX + theme.GRID_PX * 2))
        self._dark_since_s = None

    def update(self, now_s, frame):
        if frame is None or frame.brightness >= config.LOW_LIGHT_LEVEL:
            self._dark_since_s = None
        elif self._dark_since_s is None:
            self._dark_since_s = now_s

    def draw(self, screen, now_s):
        if self._dark_since_s is not None and now_s - self._dark_since_s >= config.LOW_LIGHT_DELAY_S:
            screen.blit(self._panel, self._rect)


def draw_sun(surface, center, radius_px):
    """A sun icon, so the warning reads without the words."""
    pygame.draw.circle(surface, theme.ACCENT, center, radius_px // 2)
    for index in range(SUN_RAYS):
        angle = 2 * math.pi * index / SUN_RAYS
        inner = (center[0] + math.cos(angle) * radius_px * 0.7, center[1] + math.sin(angle) * radius_px * 0.7)
        outer = (center[0] + math.cos(angle) * radius_px, center[1] + math.sin(angle) * radius_px)
        pygame.draw.line(surface, theme.ACCENT, inner, outer, theme.BORDER_PX)
