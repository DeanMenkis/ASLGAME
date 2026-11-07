"""Results after a rhythm run: score, accuracy, combo, and the signs to practise."""

import pygame

from aslgame import theme
from aslgame.game.app_flow import Action
from aslgame.game.rhythm import Judgement
from aslgame.matching.normalize import place_at
from aslgame.presentation.draw import draw_hand, draw_text_centered
from aslgame.presentation.screens.common import CONFIRM_KEYS, JUDGEMENT_TEXT, is_key, make_shade

WEAK_SIGN_PALM_PX = theme.GRID_PX * 5
WEAK_SIGN_SPACING_PX = theme.GRID_PX * 20


class ResultsScreen:
    def __init__(self, fonts, results, signs, size_px):
        self._results = results
        self._signs = signs
        self._shade = make_shade(size_px)
        counts = "   ".join(f"{JUDGEMENT_TEXT[judgement]} {results.counts[judgement]}" for judgement in Judgement)
        self._lines = [
            fonts.large.render(str(results.score), True, theme.INK),
            fonts.medium.render(f"{results.accuracy:.0%}   x{results.max_combo}", True, theme.INK),
            fonts.small.render(counts, True, theme.INK_DIM),
        ]
        self._weak_labels = [fonts.medium.render(f"{sign} {accuracy:.0%}", True, theme.INK) for sign, accuracy in results.weakest]
        self._hint = fonts.small.render("Enter  menu", True, theme.INK_DIM)

    def handle_event(self, event):
        return Action.TO_MENU if is_key(event, CONFIRM_KEYS + (pygame.K_ESCAPE,)) else None

    def update(self, now_s, result):
        return None

    def draw(self, screen, now_s, hand):
        screen.blit(self._shade, (0, 0))
        center_x_px = screen.get_width() // 2
        y_px = screen.get_height() // 4
        for surface in self._lines:
            draw_text_centered(screen, surface, (center_x_px, y_px))
            y_px += surface.get_height() + theme.GRID_PX * 2
        self._draw_weakest(screen, center_x_px, y_px + theme.GRID_PX * 16)
        draw_text_centered(screen, self._hint, (center_x_px, screen.get_height() - theme.MARGIN_PX))

    def _draw_weakest(self, screen, center_x_px, wrist_y_px):
        """The signs to practise, drawn as their outlines so they are recognised by shape."""
        count = len(self._results.weakest)
        for index, (sign, _) in enumerate(self._results.weakest):
            x_px = center_x_px + (index - (count - 1) / 2) * WEAK_SIGN_SPACING_PX
            outline = place_at(self._signs[sign].outline, (x_px, wrist_y_px, 0), WEAK_SIGN_PALM_PX, False)
            draw_hand(screen, outline, theme.GHOST, theme.LIVE_LINE_PX, theme.LIVE_JOINT_RADIUS_PX, True)
            draw_text_centered(screen, self._weak_labels[index], (x_px, wrist_y_px + theme.GRID_PX * 5))
