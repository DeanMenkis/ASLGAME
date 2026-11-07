"""Landmark normalization: removes position, size, and handedness from a hand."""

import numpy as np

from aslgame.hand import FINGER_BASES, WRIST

MIRROR_X = np.array([-1.0, 1.0, 1.0], dtype=np.float32)
MIN_PALM_SIZE = 1e-6


def palm_size(points):
    """Mean wrist-to-finger-base distance. More stable than any single bone."""
    return max(float(np.linalg.norm(points[FINGER_BASES] - points[WRIST], axis=1).mean()), MIN_PALM_SIZE)


def normalize(points, is_left):
    """Wrist at the origin, palm size 1, and left hands mirrored to look like right hands."""
    normalized = (points - points[WRIST]) / palm_size(points)
    return normalized * MIRROR_X if is_left else normalized


def place_on(normalized, points, is_left):
    """Inverse of normalize: put a normalized shape at the position, size, and side of a live hand."""
    return place_at(normalized, points[WRIST], palm_size(points), is_left)


def place_at(normalized, wrist, size, is_left):
    """Put a normalized shape with its wrist at a point and a given palm size."""
    shape = normalized * MIRROR_X if is_left else normalized
    return shape * size + wrist
