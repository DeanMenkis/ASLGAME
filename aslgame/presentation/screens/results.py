"""Results after a rhythm or music run: score, accuracy, combo, and the signs to practise."""

import pygame

from aslgame import theme
from aslgame.game.app_flow import Action
from aslgame.game.scoring import Judgement
from aslgame.presentation.draw import draw_text_centered
from aslgame.presentation.hand_shape import render_silhouette
from aslgame.presentation.screens.common import JUDGEMENT_TEXT, is_key, make_shade
from aslgame.presentation.ui import Button, make_panel

CARD_SIZE_PX = (theme.GRID_PX * 110, theme.GRID_PX * 80)
WEAK_PALM_PX = theme.GRID_PX * 5
WEAK_SPACING_PX = theme.GRID_PX * 22
BUTTON_WIDTH_PX = theme.GRID_PX * 24


class ResultsScreen:
    def __init__(self, fonts, results, signs, size_px, new_best=False):
        self._shade = make_shade(size_px)
        self._card = self._build(fonts, results, signs, new_best)
        self._card_rect = self._card.get_rect(center=(size_px[0] // 2, size_px[1] // 2))
        bottom_px = self._card_rect.bottom - theme.GRID_PX * 4 - theme.BUTTON_HEIGHT_PX
        retry = pygame.Rect(0, bottom_px, BUTTON_WIDTH_PX, theme.BUTTON_HEIGHT_PX)
        retry.right = self._card_rect.centerx - theme.GRID_PX
        menu = retry.copy()
        menu.left = self._card_rect.centerx + theme.GRID_PX
        self._buttons = [Button(fonts.body, "Retry", retry, primary=True), Button(fonts.body, "Menu", menu)]
        self._actions = [Action.RETRY, Action.TO_MENU]
        self._focus = 0

    def _build(self, fonts, results, signs, new_best):
        """The whole card is drawn once."""
        card = make_panel(CARD_SIZE_PX)
        center_x_px = CARD_SIZE_PX[0] * 3 // 5
        draw_grade_seal(card, fonts, results.grade, (theme.GRID_PX * 15, theme.GRID_PX * 16))
        if new_best:
            best = fonts.small.render("NEW BEST", True, theme.ACCENT_INK)
            tag = pygame.Rect(0, 0, best.get_width() + theme.GRID_PX * 2, best.get_height() + theme.GRID_PX)
            tag.midtop = (theme.GRID_PX * 15, theme.GRID_PX * 27)
            pygame.draw.rect(card, theme.ACCENT, tag, border_radius=theme.GRID_PX // 2)
            draw_text_centered(card, best, tag.center)
        y_px = theme.GRID_PX * 8
        for surface in (
            fonts.large.render(f"{results.score:,}", True, theme.INK),
            fonts.medium.render(f"{results.accuracy:.0%} accuracy    {results.max_combo} best combo", True, theme.INK),
            fonts.body.render(f"x{results.max_multiplier:.1f} peak    {results.words_cleared} clean words", True, theme.INK_DIM),
        ):
            draw_text_centered(card, surface, (center_x_px, y_px))
            y_px += surface.get_height() + theme.GRID_PX * 2
        y_px += draw_counts(card, fonts, results, center_x_px, y_px) + theme.GRID_PX * 2
        if results.weakest:
            y_px += theme.GRID_PX * 2
            draw_text_centered(card, fonts.small.render("PRACTISE", True, theme.ACCENT), (center_x_px, y_px))
            count = len(results.weakest)
            for index, (sign, accuracy) in enumerate(results.weakest):
                x_px = center_x_px + (index - (count - 1) / 2) * WEAK_SPACING_PX
                silhouette, wrist = render_silhouette(signs[sign].outline, WEAK_PALM_PX, False)
                wrist_y_px = y_px + theme.GRID_PX * 20
                card.blit(silhouette, (x_px - wrist[0], wrist_y_px - wrist[1]))
                label = fonts.body.render(f"{sign}  {accuracy:.0%}", True, theme.INK)
                draw_text_centered(card, label, (x_px, wrist_y_px + theme.GRID_PX * 4))
        return card

    def handle_event(self, event):
        if is_key(event, (pygame.K_r,)):
            return Action.RETRY
        if is_key(event, (pygame.K_m, pygame.K_ESCAPE)):
            return Action.TO_MENU
        if is_key(event, (pygame.K_LEFT, pygame.K_RIGHT)):
            self._focus = 1 - self._focus
        elif is_key(event, (pygame.K_RETURN, pygame.K_SPACE)):
            return self._actions[self._focus]
        for index, button in enumerate(self._buttons):
            if button.is_clicked(event):
                return self._actions[index]
        return None

    def update(self, now_s, result):
        return None

    def draw(self, screen, now_s, hand):
        screen.blit(self._shade, (0, 0))
        screen.blit(self._card, self._card_rect)
        for index, button in enumerate(self._buttons):
            button.draw(screen, focused=index == self._focus)


def draw_counts(card, fonts, results, center_x_px, y_px):
    """Judgement counts in a row, each in its judgement's color. Returns the row height."""
    pieces = [fonts.body.render(f"{JUDGEMENT_TEXT[j]} {results.counts[j]}", True, theme.JUDGEMENT_COLORS[j.name]) for j in Judgement]
    gap_px = theme.GRID_PX * 4
    x_px = center_x_px - (sum(piece.get_width() for piece in pieces) + gap_px * (len(pieces) - 1)) / 2
    for piece in pieces:
        card.blit(piece, piece.get_rect(midleft=(x_px, y_px)))
        x_px += piece.get_width() + gap_px
    return pieces[0].get_height()


GRADE_COLORS = {"S": (255, 210, 60), "A": (70, 205, 115), "B": (120, 220, 255), "C": (245, 145, 50), "D": (235, 75, 65)}


def draw_grade_seal(card, fonts, grade, center):
    """The grade stamped in a ring, like a seal: shape and letter, not color alone."""
    color = GRADE_COLORS[grade]
    radius = theme.GRID_PX * 10
    pygame.draw.circle(card, color, center, radius, theme.GRID_PX)
    pygame.draw.circle(card, color, center, radius - theme.GRID_PX * 2, 2)
    draw_text_centered(card, fonts.display.render(grade, True, color), center)
