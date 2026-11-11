"""Results after a timed run: a proof sheet with the grade, the numbers, the signs to practise, and the run's clean words printed as a poster."""

import pygame

from aslgame import theme
from aslgame.game.app_flow import Action
from aslgame.game.scoring import Judgement
from aslgame.presentation.draw import draw_text_centered
from aslgame.presentation import press
from aslgame.presentation.screens.common import JUDGEMENT_TEXT, is_key, make_shade
from aslgame.presentation.ui import Button

CARD_SIZE_PX = (theme.GRID_PX * 136, theme.GRID_PX * 80)
GRADE_RADIUS_PX = theme.GRID_PX * 10
WEAK_PALM_PX = theme.GRID_PX * 5
WEAK_SPACING_PX = theme.GRID_PX * 20
BROADSIDE_LEFT_PX = theme.GRID_PX * 84
BROADSIDE_WIDTH_PX = theme.GRID_PX * 47
BROADSIDE_MAX_LINE_PX = theme.GRID_PX * 15
BROADSIDE_GAP_PX = theme.GRID_PX
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
        left_px = self._card_rect.left + theme.GRID_PX * 5
        self._buttons = [Button(fonts.body, label, (left_px + index * step_px, bottom_px, BUTTON_WIDTH_PX, theme.BUTTON_HEIGHT_PX),
                                primary=index == 0) for index, label in enumerate(labels)]
        self._focus = 0

    def _build(self, fonts, results, signs, new_best):
        """The whole sheet is drawn once. Left: the grade, the numbers, the letters to practise.
        Right: the run's clean words set as a broadside, each line fitted to the column like wood type."""
        card = press.sticker(CARD_SIZE_PX)
        slab, label = theme.SLAB_FAMILIES, theme.LABEL_FAMILIES
        left_x_px = theme.GRID_PX * 5
        grade_center = (left_x_px + GRADE_RADIUS_PX, theme.GRID_PX * 5 + GRADE_RADIUS_PX)
        draw_grade(card, results.grade, grade_center)
        if new_best:
            star = press.starburst(theme.GRID_PX * 7, 14, theme.YELLOW, 0.84, theme.BLUE)
            words = pygame.font.SysFont(label, 30, bold=True).render("NEW BEST", True, theme.BLUE)
            draw_text_centered(star, pygame.transform.rotozoom(words, 12, 1.0), star.get_rect().center)
            card.blit(star, star.get_rect(center=(grade_center[0] + GRADE_RADIUS_PX, grade_center[1] - GRADE_RADIUS_PX + theme.GRID_PX)))
        x_px = grade_center[0] + GRADE_RADIUS_PX + theme.GRID_PX * 9
        score = pygame.font.SysFont(slab, 68, bold=True).render(f"{results.score:,}", True, theme.BLUE)
        card.blit(score, (x_px, theme.GRID_PX * 4))
        y_px = theme.GRID_PX * 4 + score.get_height()
        stat_font = pygame.font.SysFont(label, 34, bold=True)
        for text in (f"{results.accuracy:.0%} ACCURACY", f"{results.max_combo} BEST COMBO", f"×{results.max_multiplier:.1f} AT ITS HOTTEST"):
            line = stat_font.render(text, True, theme.BLUE)
            card.blit(line, (x_px, y_px))
            y_px += line.get_height()
        y_px = grade_center[1] + GRADE_RADIUS_PX + theme.GRID_PX * 5
        draw_counts(card, fonts, results, left_x_px, y_px)
        if results.weakest:
            y_px += theme.GRID_PX * 7
            card.blit(stat_font.render("PRACTISE", True, theme.RED), (left_x_px, y_px))
            for index, (sign, accuracy) in enumerate(results.weakest):
                x_px = left_x_px + index * WEAK_SPACING_PX
                drawing, _ = press.line_hand(signs[sign].outline, WEAK_PALM_PX, theme.BLUE)
                drawing = drawing.subsurface(drawing.get_bounding_rect())
                card.blit(drawing, drawing.get_rect(midbottom=(x_px + WEAK_SPACING_PX // 2 - theme.GRID_PX * 2, y_px + theme.GRID_PX * 17)))
                text = stat_font.render(f"{sign}  {accuracy:.0%}", True, theme.BLUE)
                card.blit(text, text.get_rect(midtop=(x_px + WEAK_SPACING_PX // 2 - theme.GRID_PX * 2, y_px + theme.GRID_PX * 18)))
        draw_broadside(card, results.words, pygame.Rect(BROADSIDE_LEFT_PX, theme.GRID_PX * 4, BROADSIDE_WIDTH_PX,
                                                        CARD_SIZE_PX[1] - theme.GRID_PX * 8))
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


def draw_counts(card, fonts, results, left_px, y_px):
    """Judgement counts in a row, each a small block in its judgement's ink."""
    x_px = left_px
    for judgement in Judgement:
        name = judgement.name
        label = fonts.label.render(f"{JUDGEMENT_TEXT[judgement].upper()} {results.counts[judgement]}", True, theme.JUDGEMENT_TEXT_COLORS[name])
        block = pygame.Rect(x_px, y_px, label.get_width() + theme.GRID_PX * 2, label.get_height() + theme.GRID_PX)
        pygame.draw.rect(card, theme.JUDGEMENT_COLORS[name], block, border_radius=3)
        card.blit(label, label.get_rect(center=block.center))
        x_px = block.right + theme.GRID_PX


def draw_grade(card, grade, center):
    """The grade in wood type inside a registration mark. S and A are overprinted in two inks, the rest in one;
    the letter itself is the grade, so the inks only add to it."""
    press.draw_registration(card, center, GRADE_RADIUS_PX, theme.BLUE, 4, 1.18)
    font = pygame.font.SysFont(theme.SLAB_FAMILIES, 150, bold=True)
    if grade == "S":
        letter = press.overprint_text(font, grade, theme.RED, theme.YELLOW, (7, 7), halo_px=6)
    elif grade == "A":
        letter = press.overprint_text(font, grade, theme.BLUE, theme.RED, (7, 7), halo_px=6)
    else:
        letter = press.halo_text(font, grade, theme.BLUE, halo_px=6)
    card.blit(letter, letter.get_rect(center=center))


def draw_broadside(card, words, box):
    """The words signed without a miss, printed as a poster: every line stretched to the full measure, so short
    words stand tall and long ones run small, in alternating inks. With none, the sheet stays blank but for its marks."""
    pygame.draw.line(card, theme.BLUE, (box.left - theme.GRID_PX * 3, box.top), (box.left - theme.GRID_PX * 3, box.bottom), 3)
    press.draw_crop_marks(card, box, theme.BLUE_FAINT, 10, 4)
    if not words:
        press.draw_registration(card, box.center, theme.GRID_PX * 4, theme.BLUE_FAINT, 3)
        return
    font = pygame.font.SysFont(theme.SLAB_FAMILIES, 120, bold=True)
    inks = (theme.BLUE, theme.RED)
    # Later words push earlier ones off: the sheet shows the last lines that fit.
    lines, height_px = [], 0
    for index, word in reversed(list(enumerate(words))):
        line = font.render(word, True, inks[index % 2])
        line = line.subsurface(line.get_bounding_rect())
        scale = min(box.width / line.get_width(), BROADSIDE_MAX_LINE_PX / line.get_height())
        line = pygame.transform.smoothscale(line, (int(line.get_width() * scale), int(line.get_height() * scale)))
        if height_px + line.get_height() > box.height:
            break
        lines.insert(0, line)
        height_px += line.get_height() + BROADSIDE_GAP_PX
    y_px = box.top
    for line in lines:
        card.blit(line, (box.left, y_px))
        y_px += line.get_height() + BROADSIDE_GAP_PX
