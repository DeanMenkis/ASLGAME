"""Optional keys panel, opened with H or the ? button."""

import pygame

from aslgame import theme
from aslgame.presentation.draw import draw_text_centered
from aslgame.presentation.ui import clicked, draw_key_chip, make_panel

SECTIONS = (
    ("Menu", (("Left  Right", "Mode"), ("Up  Down", "Choose"), ("Enter", "Start"), ("H", "Keys"), ("Esc", "Quit"))),
    ("Playing", (("Esc  P", "Pause"),)),
    ("Paused", (("Esc  Space", "Resume"), ("M", "Menu"))),
    ("Results", (("R", "Retry"), ("M", "Menu"))),
    ("Anywhere", (("C", "Finger colors"), ("S", "Sound"), ("F", "Fullscreen"), ("F3", "Performance"))),
)
CLOSE_KEYS = (pygame.K_ESCAPE, pygame.K_h, pygame.K_RETURN, pygame.K_SPACE)
COLUMN_WIDTH_PX = theme.GRID_PX * 40
PANEL_SIZE_PX = (COLUMN_WIDTH_PX * 2 + theme.GRID_PX * 8, theme.GRID_PX * 60)


class HelpPanel:
    def __init__(self, fonts, size_px):
        self.visible = False
        self._shade = make_panel(size_px, theme.SHADE, 0)
        self._panel = self._build(fonts)
        self._rect = self._panel.get_rect(center=(size_px[0] // 2, size_px[1] // 2))

    def _build(self, fonts):
        """Drawn once, so showing it costs a single blit."""
        panel = make_panel(PANEL_SIZE_PX, theme.SURFACE)
        draw_text_centered(panel, fonts.medium.render("Keys", True, theme.INK), (PANEL_SIZE_PX[0] // 2, theme.GRID_PX * 5))
        x_px = [theme.GRID_PX * 4, theme.GRID_PX * 4 + COLUMN_WIDTH_PX + theme.GRID_PX * 2]
        y_px = [theme.GRID_PX * 10, theme.GRID_PX * 10]
        for index, (title, rows) in enumerate(SECTIONS):
            column = 0 if index < 2 else 1
            panel.blit(fonts.small.render(title.upper(), True, theme.ACCENT), (x_px[column], y_px[column]))
            y_px[column] += theme.GRID_PX * 4
            for key, action in rows:
                center_y_px = y_px[column] + theme.GRID_PX * 2
                chip = draw_key_chip(panel, fonts.small, key, (x_px[column], center_y_px))
                label = fonts.body.render(action, True, theme.INK)
                panel.blit(label, label.get_rect(midleft=(chip.right + theme.GRID_PX * 2, center_y_px)))
                y_px[column] += theme.GRID_PX * 5
            y_px[column] += theme.GRID_PX * 2
        return panel

    def handle_event(self, event):
        """Close on a key or a click. Returns True when the event was used."""
        if not self.visible:
            return False
        if (event.type == pygame.KEYDOWN and event.key in CLOSE_KEYS) or clicked(event, pygame.Rect((0, 0), (99999, 99999))):
            self.visible = False
        return event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN)

    def draw(self, screen):
        if self.visible:
            screen.blit(self._shade, (0, 0))
            screen.blit(self._panel, self._rect)
