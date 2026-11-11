"""Results after a rhythm or music run: score, accuracy, combo, and the signs to practise."""

import pygame

from aslgame import theme
from aslgame.game.app_flow import Action
from aslgame.game.scoring import Judgement
from aslgame.presentation.draw import draw_text_centered
from aslgame.presentation import ink
from aslgame.presentation.screens.common import JUDGEMENT_TEXT, is_key, make_shade
from aslgame.presentation.ui import Button, make_panel

CARD_SIZE_PX = (theme.GRID_PX * 110, theme.GRID_PX * 80)
GRADE_RADIUS_PX = theme.GRID_PX * 11
WEAK_PALM_PX = theme.GRID_PX * 5
WEAK_SPACING_PX = theme.GRID_PX * 22
BUTTON_WIDTH_PX = theme.GRID_PX * 24
ACTIONS = {"Retry": Action.RETRY, "Practise": Action.PRACTISE, "Menu": Action.TO_MENU}


class ResultsScreen:
    def __init__(self, fonts, results, signs, size_px, new_best=False):
        self._shade = make_shade(size_px)
        self._card = self._build(fonts, results, signs, new_best)
        self._card_rect = self._card.get_rect(center=(size_px[0] // 2, size_px[1] // 2))
        bottom_px = self._card_rect.bottom - theme.GRID_PX * 4 - theme.BUTTON_HEIGHT_PX
        # Practise is offered when the run showed letters to work on.
        labels = ["Retry", "Practise", "Menu"] if results.weakest else ["Retry", "Menu"]
        self._actions = [ACTIONS[label] for label in labels]
        step_px = BUTTON_WIDTH_PX + theme.GRID_PX * 2
        left_px = self._card_rect.centerx - (step_px * len(labels) - theme.GRID_PX * 2) // 2
        self._buttons = [Button(fonts.body, label, (left_px + index * step_px, bottom_px, BUTTON_WIDTH_PX, theme.BUTTON_HEIGHT_PX),
                                primary=index == 0) for index, label in enumerate(labels)]
        self._focus = 0

    def _build(self, fonts, results, signs, new_best):
        """The whole card is drawn once: a paper sheet, the grade painted in a brushed circle, the numbers in ink."""
        card = ink.torn_slip(CARD_SIZE_PX, (*theme.PAPER, 250), seed=11)
        serif = theme.SERIF_FAMILIES
        center_x_px = CARD_SIZE_PX[0] * 3 // 5
        grade_center = (theme.GRID_PX * 17, theme.GRID_PX * 18)
        draw_grade(card, results.grade, grade_center)
        if new_best:
            best = pygame.font.SysFont(serif, 30, italic=True).render("new best", True, theme.SEAL)
            best_rect = best.get_rect(center=(grade_center[0], grade_center[1] + GRADE_RADIUS_PX + theme.GRID_PX * 5))
            card.blit(best, best_rect)
            ink.draw_brush_line(card, best_rect.left, best_rect.bottom + 2, best_rect.width, theme.SEAL, 5)
        y_px = theme.GRID_PX * 8
        for surface in (
            pygame.font.SysFont(serif, 72).render(f"{results.score:,}", True, theme.INK_BLACK),
            pygame.font.SysFont(serif, 32).render(f"{results.accuracy:.0%} accuracy    {results.max_combo} best combo", True, theme.INK_BLACK),
            pygame.font.SysFont(serif, 26, italic=True).render(f"×{results.max_multiplier:.1f} at its hottest    {results.words_cleared} clean words",
                                                               True, theme.INK_SOFT),
        ):
            draw_text_centered(card, surface, (center_x_px, y_px))
            y_px += surface.get_height() + theme.GRID_PX * 2
        y_px += draw_counts(card, fonts, results, center_x_px, y_px) + theme.GRID_PX * 2
        if results.weakest:
            y_px += theme.GRID_PX * 2
            draw_text_centered(card, pygame.font.SysFont(serif, 26, italic=True).render("practise", True, theme.SEAL), (center_x_px, y_px))
            count = len(results.weakest)
            for index, (sign, accuracy) in enumerate(results.weakest):
                x_px = center_x_px + (index - (count - 1) / 2) * WEAK_SPACING_PX
                silhouette, wrist = ink.ink_hand(signs[sign].outline, WEAK_PALM_PX, theme.INK_BLACK)
                wrist_y_px = y_px + theme.GRID_PX * 20
                card.blit(silhouette, (x_px - wrist[0], wrist_y_px - wrist[1]))
                label = pygame.font.SysFont(serif, 26).render(f"{sign}  {accuracy:.0%}", True, theme.INK_BLACK)
                draw_text_centered(card, label, (x_px, wrist_y_px + theme.GRID_PX * 4))
        return card

    def handle_event(self, event):
        if is_key(event, (pygame.K_r,)):
            return Action.RETRY
        if is_key(event, (pygame.K_m, pygame.K_ESCAPE)):
            return Action.TO_MENU
        if is_key(event, (pygame.K_p,)) and Action.PRACTISE in self._actions:
            return Action.PRACTISE
        if is_key(event, (pygame.K_LEFT, pygame.K_RIGHT)):
            self._focus = (self._focus + (1 if event.key == pygame.K_RIGHT else -1)) % len(self._buttons)
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


def draw_grade(card, grade, center):
    """The grade painted, not stamped: a brushed ensō with the letter inside in serif.
    S burns in fire colours, A is vermilion, the rest are ink; the letter itself is the grade, so colour only adds to it."""
    ink.draw_enso(card, center, GRADE_RADIUS_PX, theme.GRID_PX * 3, seed=ord(grade))
    font = pygame.font.SysFont(theme.SERIF_FAMILIES, 150, italic=True)
    if grade == "S":
        letter = ink.fire_text(font, grade, theme.FLAME_GOLD, theme.SEAL, edge_px=3)
    else:
        letter = font.render(grade, True, theme.SEAL if grade == "A" else theme.INK_BLACK)
    # Nudged right a little, since an italic letter leans left of its box.
    card.blit(letter, letter.get_rect(center=(center[0] + theme.GRID_PX // 2, center[1])))
