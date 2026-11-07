"""Karaoke strip: the word as a row of cells. Filled is done, outlined in accent is now."""

import pygame

from aslgame import theme


class Strip:
    def __init__(self, font, queue, screen_size_px):
        self._queue = queue
        self._cells = []  # one rect per sign, in queue order
        self._ink = {}
        self._inverse = {}
        width_px = sum(theme.STRIP_SPACE_PX if char == " " else theme.STRIP_CELL_PX + theme.STRIP_GAP_PX
                       for char in queue.text) - theme.STRIP_GAP_PX
        x_px = (screen_size_px[0] - width_px) // 2
        y_px = screen_size_px[1] - theme.MARGIN_PX - theme.STRIP_CELL_PX
        for char in queue.text:
            if char == " ":
                x_px += theme.STRIP_SPACE_PX
                continue
            self._cells.append(pygame.Rect(x_px, y_px, theme.STRIP_CELL_PX, theme.STRIP_CELL_PX))
            x_px += theme.STRIP_CELL_PX + theme.STRIP_GAP_PX
            # Rendered once here so drawing never renders text.
            self._ink[char] = font.render(char, True, theme.INK)
            self._inverse[char] = font.render(char, True, theme.BACKGROUND)
        self.top_px = y_px

    def draw(self, screen):
        for sign_index, rect in enumerate(self._cells):
            char = self._queue.text[self._queue.positions[sign_index]]
            if sign_index < self._queue.current:
                pygame.draw.rect(screen, theme.INK, rect)
                label = self._inverse[char]
            elif sign_index == self._queue.current:
                pygame.draw.rect(screen, theme.ACCENT, rect, theme.STRIP_CURRENT_LINE_PX)
                label = self._ink[char]
            else:
                pygame.draw.rect(screen, theme.INK_DIM, rect, theme.STRIP_LINE_PX)
                label = self._ink[char]
            screen.blit(label, label.get_rect(center=rect.center))
