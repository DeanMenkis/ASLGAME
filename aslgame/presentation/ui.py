"""GUI controls: panels, buttons, and key chips. Mouse and keyboard both work."""

import pygame

from aslgame import theme


def make_panel(size_px, color=theme.SURFACE, radius_px=theme.CORNER_PX):
    """A rounded, translucent card. Made once and blitted each frame."""
    panel = pygame.Surface(size_px, pygame.SRCALPHA)
    pygame.draw.rect(panel, color, panel.get_rect(), border_radius=radius_px)
    return panel


def clicked(event, rect):
    return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and rect.collidepoint(event.pos)


class Button:
    """A rounded button. Focused (keyboard) or hovered (mouse) buttons are raised; primary buttons are filled with accent."""

    def __init__(self, font, label, rect, primary=False, enabled=True):
        self.rect = pygame.Rect(rect)
        self.primary = primary
        self.enabled = enabled
        ink = theme.ACCENT_INK if primary else theme.INK
        self._label = font.render(label, True, ink)
        self._disabled_label = font.render(label, True, theme.DISABLED)

    def is_clicked(self, event):
        return self.enabled and clicked(event, self.rect)

    def is_hovered(self):
        return self.enabled and self.rect.collidepoint(pygame.mouse.get_pos())

    def draw(self, screen, focused=False):
        active = focused or self.is_hovered()
        if not self.enabled:
            pygame.draw.rect(screen, theme.SURFACE_RAISED, self.rect, theme.BORDER_PX, border_radius=theme.CORNER_PX)
            screen.blit(self._disabled_label, self._disabled_label.get_rect(center=self.rect.center))
            return
        if self.primary:
            pygame.draw.rect(screen, theme.ACCENT, self.rect, border_radius=theme.CORNER_PX)
            if active:
                pygame.draw.rect(screen, theme.INK, self.rect, theme.BORDER_PX, border_radius=theme.CORNER_PX)
        else:
            pygame.draw.rect(screen, theme.SURFACE_HOVER if active else theme.SURFACE_RAISED, self.rect, border_radius=theme.CORNER_PX)
            border = theme.ACCENT if focused else theme.BORDER
            pygame.draw.rect(screen, border, self.rect, theme.BORDER_PX, border_radius=theme.CORNER_PX)
        screen.blit(self._label, self._label.get_rect(center=self.rect.center))


def button_width(font, label):
    return font.size(label)[0] + theme.BUTTON_PADDING_PX * 2


def stack_buttons(font, labels, center_x_px, top_px, width_px=None):
    """Buttons in a column on the grid, all the same width."""
    width_px = width_px or max(button_width(font, label) for label in labels)
    buttons = []
    for index, label in enumerate(labels):
        rect = pygame.Rect(0, 0, width_px, theme.BUTTON_HEIGHT_PX)
        rect.midtop = (center_x_px, top_px + index * (theme.BUTTON_HEIGHT_PX + theme.GRID_PX * 2))
        buttons.append(Button(font, label, rect, primary=index == 0))
    return buttons


def draw_key_chip(screen, font, text, midleft_px):
    """A key cap with its name, so a key reads as a key."""
    label = font.render(text, True, theme.INK)
    width_px = max(theme.KEY_CHIP_MIN_WIDTH_PX, label.get_width() + theme.GRID_PX * 2)
    rect = pygame.Rect(0, 0, width_px, label.get_height() + theme.GRID_PX)
    rect.midleft = midleft_px
    pygame.draw.rect(screen, theme.SURFACE_RAISED, rect, border_radius=theme.GRID_PX)
    pygame.draw.rect(screen, theme.BORDER, rect, theme.BORDER_PX, border_radius=theme.GRID_PX)
    screen.blit(label, label.get_rect(center=rect.center))
    return rect


class Toggle:
    """An on/off control. The state is spelled out as well as filled, so it never rests on color alone."""

    def __init__(self, font, label, rect):
        self.rect = pygame.Rect(rect)
        self._on = Button(font, f"{label}  On", self.rect, primary=True)
        self._off = Button(font, f"{label}  Off", self.rect)

    def is_clicked(self, event):
        return clicked(event, self.rect)

    def draw(self, screen, on):
        (self._on if on else self._off).draw(screen)
