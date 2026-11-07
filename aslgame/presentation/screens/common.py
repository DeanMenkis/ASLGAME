"""Helpers shared by the screens."""

import pygame

from aslgame import theme
from aslgame.game.rhythm import Judgement
from aslgame.matching import matcher
from aslgame.matching.normalize import normalize, place_at, place_on
from aslgame.presentation.draw import draw_hand

RING_CENTER_PX = (theme.MARGIN_PX + theme.RING_RADIUS_PX, theme.MARGIN_PX + theme.RING_RADIUS_PX)
CONFIRM_KEYS = (pygame.K_RETURN, pygame.K_SPACE)
PAUSE_KEYS = (pygame.K_ESCAPE, pygame.K_p)
JUDGEMENT_TEXT = {Judgement.PERFECT: "Perfect", Judgement.GOOD: "Good", Judgement.OK: "OK", Judgement.MISS: "Miss"}


def is_key(event, keys):
    return event.type == pygame.KEYDOWN and event.key in keys


def make_shade(size_px):
    shade = pygame.Surface(size_px, pygame.SRCALPHA)
    shade.fill(theme.SHADE)
    return shade


def idle_wrist(size_px):
    """Where the ghost's wrist sits when no hand is seen."""
    return (size_px[0] / 2 + theme.IDLE_GHOST_OFFSET_PX[0], size_px[1] / 2 + theme.IDLE_GHOST_OFFSET_PX[1], 0)


class TargetScorer:
    """Scores the live hand against a target, once per tracking result rather than once per frame."""

    def __init__(self, signs):
        self._signs = signs
        self._result = None
        self._target = None
        self.score = 0.0

    def update(self, result, target_name):
        if result is self._result and target_name == self._target:
            return self.score
        self._result, self._target = result, target_name
        hand = result.hand if result else None
        if hand is None:
            self.score = 0.0
        else:
            self.score = matcher.target_score(normalize(hand.points_px, hand.is_left), self._signs[target_name], self._signs)
        return self.score


def draw_live_hand(screen, hand):
    if hand is not None:
        draw_hand(screen, hand.points_px, theme.LIVE_HAND, theme.LIVE_LINE_PX, theme.LIVE_JOINT_RADIUS_PX, True)


def ghost_points(sign, hand, idle_wrist_px):
    if hand is not None:
        return place_on(sign.outline, hand.points_px, hand.is_left)
    return place_at(sign.outline, idle_wrist_px, theme.IDLE_GHOST_PALM_PX, False)


def draw_ghost(screen, ghost_px, matched):
    draw_hand(screen, ghost_px, theme.GHOST, theme.GHOST_LINE_PX, theme.GHOST_JOINT_RADIUS_PX, matched)
