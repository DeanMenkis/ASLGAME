"""Helpers shared by the screens: scoring the target, the ghost, the reference card, and the top bar."""

import pygame

from aslgame import config, theme
from aslgame.game.rhythm import Judgement
from aslgame.hand import FINGERS, WRIST
from aslgame.matching import matcher
from aslgame.matching.normalize import normalize, palm_size
from aslgame.presentation.draw import draw_text_centered
from aslgame.presentation.hand_shape import GhostRenderer, draw_finger_fixes, render_silhouette
from aslgame.presentation.ui import clicked, make_panel

CONFIRM_KEYS = (pygame.K_RETURN, pygame.K_SPACE)
PAUSE_KEYS = (pygame.K_ESCAPE, pygame.K_p)
JUDGEMENT_TEXT = {Judgement.PERFECT: "Perfect", Judgement.GOOD: "Good", Judgement.OK: "OK", Judgement.MISS: "Miss"}
CARD_TOPLEFT_PX = (theme.MARGIN_PX, theme.TOP_BAR_HEIGHT_PX + theme.GRID_PX * 2)


def is_key(event, keys):
    return event.type == pygame.KEYDOWN and event.key in keys


def make_shade(size_px):
    return make_panel(size_px, theme.SHADE, 0)


def idle_wrist(size_px):
    """Where the ghost's wrist sits when no hand is seen."""
    return (size_px[0] / 2 + theme.IDLE_GHOST_OFFSET_PX[0], size_px[1] / 2 + theme.IDLE_GHOST_OFFSET_PX[1])


class TargetScorer:
    """Scores the live hand against a target once per tracking result, and finds the fingers to fix."""

    def __init__(self, signs):
        self._signs = signs
        self._result = None
        self._target = None
        self.score = 0.0
        self.fingers_off = []

    def update(self, result, target_name):
        if result is self._result and target_name == self._target:
            return self.score
        self._result, self._target = result, target_name
        hand = result.hand if result else None
        if hand is None:
            self.score, self.fingers_off = 0.0, []
            return self.score
        target = self._signs[target_name]
        normalized = normalize(hand.points_px, hand.is_left)
        self.score = matcher.target_score(normalized, target, self._signs)
        self.fingers_off = [] if self.score >= config.MATCH_THRESHOLD else matcher.fingers_off(normalized, target)
        return self.score


class Ghost:
    """The target sign drawn as a silhouette over the live hand, or in the middle when no hand is seen."""

    def __init__(self, size_px, settings):
        self._renderer = GhostRenderer()
        self._idle_wrist = idle_wrist(size_px)
        self._settings = settings

    def draw(self, screen, sign, hand, matched, fingers_off):
        colors = self._settings.finger_colors
        if hand is None:
            self._renderer.draw(screen, sign, self._idle_wrist, theme.IDLE_GHOST_PALM_PX, False, False, colors)
            return
        wrist = hand.points_px[WRIST, :2].tolist()
        self._renderer.draw(screen, sign, wrist, palm_size(hand.points_px), hand.is_left, matched, colors)
        if fingers_off:
            # Marked on the player's own fingers; the ghost already shows where they should go.
            draw_finger_fixes(screen, hand.points_px, fingers_off)


class ReferenceCard:
    """A large, still picture of the target sign, so the shape is clear even while the hand moves."""

    def __init__(self, fonts, signs, names, settings):
        # Both color styles are built up front so switching never renders in the loop.
        self._cards = {(name, colors): self._build(fonts, signs[name], colors) for name in names for colors in (False, True)}
        self._settings = settings

    def _build(self, fonts, sign, finger_colors):
        card = make_panel(theme.REFERENCE_CARD_SIZE_PX)
        width_px, height_px = theme.REFERENCE_CARD_SIZE_PX
        draw_text_centered(card, fonts.large.render(sign.name, True, theme.INK), (width_px // 2, theme.GRID_PX * 6))
        silhouette, wrist = render_silhouette(sign.outline, theme.REFERENCE_PALM_PX, False, finger_colors)
        bottom_px = height_px - theme.GRID_PX * 4
        # Placed by the wrist, then pulled back inside the card if the shape runs over an edge.
        rect = silhouette.get_rect(topleft=(width_px // 2 - wrist[0], bottom_px - wrist[1] - theme.REFERENCE_PALM_PX))
        rect.clamp_ip(pygame.Rect(0, theme.GRID_PX * 11, width_px, height_px - theme.GRID_PX * 12))
        card.blit(silhouette, rect)
        return card

    def draw(self, screen, name, progress=None):
        """progress, from 0 to 1, fills a bar along the card's bottom edge."""
        card = self._cards[(name, self._settings.finger_colors)]
        rect = screen.blit(card, CARD_TOPLEFT_PX)
        if progress:
            fill = pygame.Rect(rect.left, rect.bottom - theme.GRID_PX, int(rect.width * min(1.0, progress)), theme.GRID_PX)
            pygame.draw.rect(screen, theme.ACCENT, fill, border_radius=theme.GRID_PX // 2)


class TopBar:
    """The bar along the top of play screens, with a pause button at the right."""

    def __init__(self, size_px):
        self._panel = make_panel((size_px[0], theme.TOP_BAR_HEIGHT_PX), theme.SURFACE, 0)
        self.pause_rect = pygame.Rect(0, 0, theme.ICON_BUTTON_PX, theme.ICON_BUTTON_PX)
        self.pause_rect.midright = (size_px[0] - theme.MARGIN_PX, theme.TOP_BAR_HEIGHT_PX // 2)

    def pause_clicked(self, event):
        return clicked(event, self.pause_rect)

    def draw(self, screen):
        screen.blit(self._panel, (0, 0))
        hovered = self.pause_rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(screen, theme.SURFACE_HOVER if hovered else theme.SURFACE_RAISED, self.pause_rect, border_radius=theme.CORNER_PX)
        bar = pygame.Rect(0, 0, theme.GRID_PX, theme.ICON_BUTTON_PX // 2)
        for offset_px in (-theme.GRID_PX, theme.GRID_PX):
            bar.center = (self.pause_rect.centerx + offset_px, self.pause_rect.centery)
            pygame.draw.rect(screen, theme.INK, bar, border_radius=theme.GRID_PX // 4)


class FixHint:
    """Names the fingers to fix, one per line under the reference card. Each name is rendered once."""

    def __init__(self, fonts):
        self._names = {name: fonts.body.render(name, True, theme.FINGER_FIX) for name in FINGERS}
        self._center_x_px = CARD_TOPLEFT_PX[0] + theme.REFERENCE_CARD_SIZE_PX[0] // 2
        self._top_px = CARD_TOPLEFT_PX[1] + theme.REFERENCE_CARD_SIZE_PX[1] + theme.GRID_PX * 2

    def draw(self, screen, fingers_off):
        y_px = self._top_px
        for name in fingers_off:
            surface = self._names[name]
            screen.blit(surface, surface.get_rect(midtop=(self._center_x_px, y_px)))
            y_px += surface.get_height()
