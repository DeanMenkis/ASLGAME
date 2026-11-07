"""Scores a normalized hand against sign templates."""

import numpy as np

from aslgame import config
from aslgame.hand import FINGERS


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


def target_score(hand, target, signs):
    """Score against the target, or 0.0 when another sign fits clearly better. Stops look-alikes passing."""
    target_value = score(hand, target.samples)
    for sign in signs.values():
        if sign.name != target.name and score(hand, sign.samples) > target_value + config.MATCH_RIVAL_MARGIN:
            return 0.0
    return target_value


def fingers_off(hand, target):
    """Names of the fingers whose joints sit clearly away from the target's outline."""
    return [name for name, joints in FINGERS.items()
            if np.linalg.norm(hand[list(joints[1:])] - target.outline[list(joints[1:])], axis=1).mean() > config.FINGER_HINT_LIMIT]
