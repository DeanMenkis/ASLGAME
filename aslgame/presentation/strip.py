"""Word strip: the words as paper tiles. Ink-filled is done, a vermilion frame is now, plain paper is next.

Judged tiles take their judgement's dye with dots for the grade (3, 2, 1), or a struck-through grey tile for a miss.
Long text scrolls so the current tile stays in view.
"""

import pygame

from aslgame import theme

CELL_STEP_PX = theme.STRIP_CELL_PX + theme.STRIP_GAP_PX


class Strip:
    def __init__(self, font, queue, screen_size_px):
        self._queue = queue
        self._ink = {}
        self._paper = {}
        self._cell_x = []  # left edge of each sign's tile, in the full unscrolled layout
        x_px = 0
        for char in queue.text:
            if char == " ":
                x_px += theme.STRIP_SPACE_PX
                continue
            self._cell_x.append(x_px)
            x_px += CELL_STEP_PX
            # Rendered once here so drawing never renders text.
            self._ink[char] = font.render(char, True, theme.INK_BLACK)
            self._paper[char] = font.render(char, True, theme.PAPER)
        self._width_px = x_px - theme.STRIP_GAP_PX
        self._view_width_px = min(self._width_px, screen_size_px[0] - theme.MARGIN_PX * 2)
        self._view_left_px = (screen_size_px[0] - self._view_width_px) // 2
        self.top_px = screen_size_px[1] - theme.MARGIN_PX - theme.STRIP_CELL_PX
        pad = theme.STRIP_CURRENT_LINE_PX + 2
        self._clip = pygame.Rect(self._view_left_px - pad, self.top_px - pad, self._view_width_px + pad * 2, theme.STRIP_CELL_PX + pad * 2)

    def _scroll_px(self):
        """Shift so the current tile sits in the middle, without scrolling past either end."""
        if self._width_px <= self._view_width_px:
            return 0
        current = min(self._queue.current, len(self._cell_x) - 1)
        wanted = self._cell_x[current] + theme.STRIP_CELL_PX // 2 - self._view_width_px // 2
        return max(0, min(self._width_px - self._view_width_px, wanted))

    def draw(self, screen, judgements=None):
        """judgements, when given, holds the Judgement of each finished sign, in order."""
        scroll_px = self._scroll_px()
        previous_clip = screen.get_clip()
        screen.set_clip(self._clip)
        for sign_index, cell_x in enumerate(self._cell_x):
            left_px = self._view_left_px + cell_x - scroll_px
            if left_px + theme.STRIP_CELL_PX < self._clip.left or left_px > self._clip.right:
                continue
            rect = pygame.Rect(left_px, self.top_px, theme.STRIP_CELL_PX, theme.STRIP_CELL_PX)
            char = self._queue.text[self._queue.positions[sign_index]]
            if judgements is not None and sign_index < len(judgements):
                draw_judged_cell(screen, rect, judgements[sign_index].name, self._paper[char], self._ink[char])
                continue
            if sign_index < self._queue.current:
                pygame.draw.rect(screen, theme.INK_BLACK, rect, border_radius=3)
                label = self._paper[char]
            else:
                pygame.draw.rect(screen, theme.PAPER, rect, border_radius=3)
                if sign_index == self._queue.current:
                    pygame.draw.rect(screen, theme.SEAL, rect.inflate(6, 6), theme.STRIP_CURRENT_LINE_PX, border_radius=4)
                label = self._ink[char]
            screen.blit(label, label.get_rect(center=rect.center))
        screen.set_clip(previous_clip)


def draw_judged_cell(screen, rect, judgement_name, paper_label, ink_label):
    """A finished sign in its judgement's dye, with paper dots for hits and a strike for a miss."""
    color = theme.JUDGEMENT_COLORS[judgement_name]
    dots = theme.JUDGEMENT_DOTS[judgement_name]
    if dots == 0:
        pygame.draw.rect(screen, theme.PAPER_SHADE, rect, border_radius=3)
        screen.blit(ink_label, ink_label.get_rect(center=rect.center))
        pygame.draw.line(screen, color, rect.bottomleft, rect.topright, theme.STRIP_CURRENT_LINE_PX)
        return
    pygame.draw.rect(screen, color, rect, border_radius=3)
    screen.blit(paper_label, paper_label.get_rect(center=(rect.centerx, rect.centery - theme.STRIP_LABEL_LIFT_PX)))
    dot_y_px = rect.bottom - theme.STRIP_DOT_RADIUS_PX * 3
    first_x_px = rect.centerx - (dots - 1) * theme.STRIP_DOT_STEP_PX / 2
    for index in range(dots):
        pygame.draw.circle(screen, theme.PAPER, (first_x_px + index * theme.STRIP_DOT_STEP_PX, dot_y_px), theme.STRIP_DOT_RADIUS_PX)
