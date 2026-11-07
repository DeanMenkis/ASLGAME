"""Motion signs: a handshape held while a fingertip draws a path in the air (J and Z)."""

from dataclasses import dataclass, field
from enum import Enum, auto

import numpy as np

from aslgame import config
from aslgame.signs import Sign

MIRROR_X = np.array([-1.0, 1.0])


@dataclass(frozen=True)
class MotionSign:
    name: str
    shape: str  # the still sign whose outline is shown
    extended: frozenset  # the straight fingers of the handshape held while drawing
    tip: int  # landmark that draws the path
    path: np.ndarray  # (K, 2) corners in palm sizes, image axes (y down), right hand in the mirrored view


MOTION_SIGNS = {
    # J: the I handshape; the pinky drops, then hooks across.
    "J": MotionSign("J", "I", frozenset({"Pinky"}), 20, np.array([(0.0, 0.0), (0.0, 1.0), (-0.15, 1.35), (-0.5, 1.45), (-0.8, 1.2)])),
    # Z: the index finger draws a Z: across, diagonal back, across.
    "Z": MotionSign("Z", "Z", frozenset({"Index"}), 8, np.array([(0.0, 0.0), (1.2, 0.0), (0.0, 1.2), (1.2, 1.2)])),
}


def with_motion_letters(signs):
    """Add J, which borrows the I outline for its picture. Z has its own recorded outline."""
    letters = dict(signs)
    for name, motion in MOTION_SIGNS.items():
        if name not in letters and motion.shape in signs:
            shape = signs[motion.shape]
            letters[name] = Sign(name, shape.samples, shape.outline)
    return dict(sorted(letters.items()))


def oriented_path(motion, is_left):
    return motion.path * MIRROR_X if is_left else motion.path


def resample(points, count):
    """count points spaced evenly along the path, so drawing speed does not matter."""
    steps = np.linalg.norm(np.diff(points, axis=0), axis=1)
    distance = np.concatenate([[0.0], np.cumsum(steps)])
    if distance[-1] <= 0:
        return np.repeat(points[:1], count, axis=0)
    targets = np.linspace(0.0, distance[-1], count)
    return np.stack([np.interp(targets, distance, points[:, axis]) for axis in (0, 1)], axis=1)


def normalize_path(points):
    """Start at the origin and scale to unit size, so only the path's shape is compared."""
    shifted = points - points[0]
    size = max(np.ptp(shifted[:, 0]), np.ptp(shifted[:, 1]), 1e-6)
    return shifted / size


def path_distance(drawn, template):
    """Mean distance between two paths after resampling and normalizing. 0 is identical."""
    a = normalize_path(resample(drawn, config.MOTION_RESAMPLE_POINTS))
    b = normalize_path(resample(template, config.MOTION_RESAMPLE_POINTS))
    return float(np.linalg.norm(a - b, axis=1).mean())


def extent(points):
    return float(max(np.ptp(points[:, 0]), np.ptp(points[:, 1])))


class MotionState(Enum):
    NO_HAND = auto()
    SHAPING = auto()
    DRAWING = auto()
    DONE = auto()


@dataclass
class MotionTracker:
    """Collects the fingertip path while the handshape is held, and spots the letter's path in it."""

    motion: MotionSign
    state: MotionState = MotionState.NO_HAND
    times: list = field(default_factory=list)
    points: list = field(default_factory=list)  # fingertip positions in palm sizes
    shape_lost_s: float | None = None


def update(tracker, time_s, shape_ok, tip_palms, is_left):
    """The motion state machine. tip_palms is None when no hand is seen. Returns the state."""
    if tracker.state == MotionState.DONE:
        return tracker.state
    if tip_palms is None:
        tracker.state = MotionState.NO_HAND
        tracker.times.clear()
        tracker.points.clear()
        return tracker.state
    if tracker.state != MotionState.DRAWING:
        if not shape_ok:
            tracker.state = MotionState.SHAPING
            return tracker.state
        tracker.state = MotionState.DRAWING
        tracker.shape_lost_s = None
    # The hand turns while drawing, so the shape may slip briefly without ending the stroke.
    if shape_ok:
        tracker.shape_lost_s = None
    elif tracker.shape_lost_s is None:
        tracker.shape_lost_s = time_s
    elif time_s - tracker.shape_lost_s > config.MOTION_SHAPE_GRACE_S:
        tracker.state = MotionState.SHAPING
        tracker.times.clear()
        tracker.points.clear()
        return tracker.state
    tracker.times.append(time_s)
    tracker.points.append(tip_palms)
    while tracker.times and time_s - tracker.times[0] > config.MOTION_WINDOW_S:
        tracker.times.pop(0)
        tracker.points.pop(0)
    if found_path(tracker, is_left):
        tracker.state = MotionState.DONE
    return tracker.state


def found_path(tracker, is_left):
    """True when some recent stretch of the stroke has the letter's path shape and is big enough."""
    if len(tracker.points) < config.MOTION_MIN_POINTS:
        return False
    points = np.asarray(tracker.points)
    template = oriented_path(tracker.motion, is_left)
    for start in range(0, len(points) - config.MOTION_MIN_POINTS + 1, config.MOTION_START_STEP):
        stroke = points[start:]
        if extent(stroke) >= config.MOTION_MIN_EXTENT_PALMS and path_distance(stroke, template) <= config.MOTION_MATCH_DISTANCE:
            return True
    return False
