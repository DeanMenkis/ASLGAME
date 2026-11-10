"""Settings panel: finger colors, sound, and the About page. Opened from the menu."""

import pygame

from aslgame import theme
from aslgame.presentation.draw import draw_text_centered
from aslgame.presentation.screens.common import is_key, make_shade
from aslgame.presentation.ink import torn_slip
from aslgame.presentation.ui import Button, Toggle

PANEL_SIZE_PX = (theme.GRID_PX * 48, theme.GRID_PX * 60)
ROW_WIDTH_PX = theme.GRID_PX * 36
TOGGLES = (("finger_colors", "Finger colors"), ("sound", "Sound"), ("fire", "Fire"))


class SettingsPanel:
    def __init__(self, fonts, settings, size_px):
        self.visible = False
        self.wants_about = False
        self._settings = settings
        self._shade = make_shade(size_px)
        self._panel = torn_slip(PANEL_SIZE_PX, theme.SURFACE, seed=21)
        self._rect = self._panel.get_rect(center=(size_px[0] // 2, size_px[1] // 2))
        draw_text_centered(self._panel, fonts.medium.render("Settings", True, theme.INK), (PANEL_SIZE_PX[0] // 2, theme.GRID_PX * 6))
        rows = []
        top_px = self._rect.top + theme.GRID_PX * 12
        for index in range(len(TOGGLES) + 2):
            rect = pygame.Rect(0, 0, ROW_WIDTH_PX, theme.BUTTON_HEIGHT_PX)
            rect.midtop = (self._rect.centerx, top_px + index * (theme.BUTTON_HEIGHT_PX + theme.GRID_PX * 2))
            rows.append(rect)
        self._toggles = [(name, Toggle(fonts.body, label, rows[index])) for index, (name, label) in enumerate(TOGGLES)]
        self._about = Button(fonts.body, "About", rows[len(TOGGLES)])
        self._done = Button(fonts.body, "Done", rows[len(TOGGLES) + 1])
        self._focus = 0

    def open(self):
        self.visible = True
        self._focus = 0

    def handle_event(self, event):
        """Returns True when the event was used. Sets wants_about when About is chosen."""
        if not self.visible:
            return False
        count = len(self._toggles) + 2
        if is_key(event, (pygame.K_ESCAPE,)):
            self.visible = False
        elif is_key(event, (pygame.K_UP,)):
            self._focus = (self._focus - 1) % count
        elif is_key(event, (pygame.K_DOWN,)):
            self._focus = (self._focus + 1) % count
        elif is_key(event, (pygame.K_RETURN, pygame.K_SPACE)):
            self._press(self._focus)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            for index, rect in enumerate(self._rects()):
                if rect.collidepoint(event.pos):
                    self._press(index)
        return event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN)

    def _rects(self):
        return [toggle.rect for _, toggle in self._toggles] + [self._about.rect, self._done.rect]

    def _press(self, index):
        if index < len(self._toggles):
            name = self._toggles[index][0]
            setattr(self._settings, name, not getattr(self._settings, name))
        elif index == len(self._toggles):
            self.visible = False
            self.wants_about = True
        else:
            self.visible = False

    def draw(self, screen):
        if not self.visible:
            return
        screen.blit(self._shade, (0, 0))
        screen.blit(self._panel, self._rect)
        for index, (name, toggle) in enumerate(self._toggles):
            toggle.draw(screen, getattr(self._settings, name))
            if index == self._focus:
                pygame.draw.rect(screen, theme.INK, toggle.rect.inflate(theme.GRID_PX, theme.GRID_PX), theme.BORDER_PX,
                                 border_radius=theme.CORNER_PX)
        self._about.draw(screen, focused=self._focus == len(self._toggles))
        self._done.draw(screen, focused=self._focus == len(self._toggles) + 1)
