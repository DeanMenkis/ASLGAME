"""Results after a rhythm or music run: score, accuracy, combo, and the signs to practise."""

import pygame

from aslgame import theme
from aslgame.game.app_flow import Action
from aslgame.game.rhythm import Judgement
from aslgame.presentation.draw import draw_text_centered
from aslgame.presentation.hand_shape import render_silhouette
from aslgame.presentation.screens.common import JUDGEMENT_TEXT, is_key, make_shade
from aslgame.presentation.ui import Button, make_panel

CARD_SIZE_PX = (theme.GRID_PX * 90, theme.GRID_PX * 78)
WEAK_PALM_PX = theme.GRID_PX * 5
WEAK_SPACING_PX = theme.GRID_PX * 22
BUTTON_WIDTH_PX = theme.GRID_PX * 24


class ResultsScreen:
    def __init__(self, fonts, results, signs, size_px):
        self._shade = make_shade(size_px)
        self._card = self._build(fonts, results, signs)
        self._card_rect = self._card.get_rect(center=(size_px[0] // 2, size_px[1] // 2))
        bottom_px = self._card_rect.bottom - theme.GRID_PX * 4 - theme.BUTTON_HEIGHT_PX
        retry = pygame.Rect(0, bottom_px, BUTTON_WIDTH_PX, theme.BUTTON_HEIGHT_PX)
        retry.right = self._card_rect.centerx - theme.GRID_PX
        menu = retry.copy()
        menu.left = self._card_rect.centerx + theme.GRID_PX
        self._buttons = [Button(fonts.body, "Retry", retry, primary=True), Button(fonts.body, "Menu", menu)]
        self._actions = [Action.RETRY, Action.TO_MENU]
        self._focus = 0

    def _build(self, fonts, results, signs):
        """The whole card is drawn once."""
        card = make_panel(CARD_SIZE_PX)
        center_x_px = CARD_SIZE_PX[0] // 2
        y_px = theme.GRID_PX * 8
        for surface in (
            fonts.large.render(str(results.score), True, theme.INK),
            fonts.medium.render(f"{results.accuracy:.0%} accuracy    x{results.max_combo} best combo", True, theme.INK),
            fonts.body.render("    ".join(f"{JUDGEMENT_TEXT[j]} {results.counts[j]}" for j in Judgement), True, theme.INK_DIM),
        ):
            draw_text_centered(card, surface, (center_x_px, y_px))
            y_px += surface.get_height() + theme.GRID_PX * 2
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
