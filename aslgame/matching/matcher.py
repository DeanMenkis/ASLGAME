"""Scores a normalized hand against sign templates."""

import numpy as np

from aslgame import config


def distance(hand, samples):
    """Mean joint distance from a (21, 3) hand to the closest of (N, 21, 3) samples."""
    return float(np.linalg.norm(samples - hand, axis=2).mean(axis=1).min())


def score(hand, samples):
    """1.0 for an exact match, falling linearly to 0.0 at MATCH_ZERO_SCORE_DISTANCE."""
    return max(0.0, 1.0 - distance(hand, samples) / config.MATCH_ZERO_SCORE_DISTANCE)


def best_match(hand, signs):
    """Return (name, score) of the best scoring sign, or (None, 0.0) if there are none."""
    best_name, best_score = None, 0.0
    for sign in signs.values():
        sign_score = score(hand, sign.samples)
        if sign_score > best_score:
            best_name, best_score = sign.name, sign_score
    return best_name, best_score
