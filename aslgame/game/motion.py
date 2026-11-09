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
    checkpoints: tuple  # corners of the path the fingertip must pass, in order


MOTION_SIGNS = {
    # J: the I handshape; the pinky drops, then hooks across.
    "J": MotionSign("J", "I", frozenset({"Pinky"}), 20,
                    np.array([(0.0, 0.0), (0.0, 1.0), (-0.15, 1.35), (-0.5, 1.45), (-0.8, 1.2)]), (1, 4)),
    # Z: the index finger draws a Z: across, diagonal back, across.
    "Z": MotionSign("Z", "Z", frozenset({"Index"}), 8, np.array([(0.0, 0.0), (1.2, 0.0), (0.0, 1.2), (1.2, 1.2)]), (1, 2, 3)),
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


def smooth(points):
    """A short moving average, which calms tracking jitter without rounding the corners away."""
    count = config.MOTION_SMOOTH_POINTS
    if len(points) < count:
        return points
    kernel = np.ones(count) / count
    return np.stack([np.convolve(points[:, axis], kernel, mode="valid") for axis in (0, 1)], axis=1)


def normalize_path(points):
    """Center the path and scale each axis to unit size, so a wide, tall, big, or small drawing compares alike."""
    centered = points - points.mean(axis=0)
    extents = np.ptp(centered, axis=0)
    largest = max(float(extents.max()), 1e-6)
    # A nearly straight line keeps its thin axis thin instead of being blown up to full size.
    return centered / np.maximum(extents, largest / config.MOTION_MAX_STRETCH)


def prepare(path):
    return normalize_path(resample(path, config.MOTION_RESAMPLE_POINTS))


def path_distance(drawn, template):
    """Mean distance between two paths after resampling and normalizing. 0 is identical."""
    return prepared_distance(drawn, prepare(template))


def prepared_distance(drawn, prepared_template):
    return float(np.linalg.norm(prepare(drawn) - prepared_template, axis=1).mean())


def extent(points):
    return float(max(np.ptp(points[:, 0]), np.ptp(points[:, 1])))


class MotionState(Enum):
    NO_HAND = auto()
    SHAPING = auto()
    DRAWING = auto()
    DONE = auto()


@dataclass
class MotionTracker:
    """Follows the fingertip while the handshape is held, and spots the letter in what it draws.

    A stroke passes in either of two ways: its shape matches the letter's path wherever and however
    large it is drawn, or the fingertip touches the checkpoints of the guide on screen in order.
    """

    motion: MotionSign
    state: MotionState = MotionState.NO_HAND
    times: list = field(default_factory=list)
    points: list = field(default_factory=list)  # fingertip positions in pixels
    palms: list = field(default_factory=list)  # palm size in pixels at each point
    shape_lost_s: float | None = None
    anchor_px: np.ndarray | None = None  # where the guide's start is pinned
    anchor_palm_px: float = 1.0
    reached: int = 0  # checkpoints touched so far
    progress_s: float = 0.0


def clear(tracker):
    tracker.times.clear()
    tracker.points.clear()
    tracker.palms.clear()
    tracker.anchor_px = None
    tracker.reached = 0


def place_guide(tracker, time_s, tip_px, palm_px):
    tracker.anchor_px = np.asarray(tip_px, dtype=float)
    tracker.anchor_palm_px = palm_px
    tracker.reached = 0
    tracker.progress_s = time_s


def checkpoint_px(tracker, index, is_left):
    corner = oriented_path(tracker.motion, is_left)[tracker.motion.checkpoints[index]]
    return tracker.anchor_px + corner * tracker.anchor_palm_px


def update(tracker, time_s, shape_ok, tip_px, palm_px, is_left):
    """The motion state machine. tip_px is None when no hand is seen. Returns the state."""
    if tracker.state == MotionState.DONE:
        return tracker.state
    if tip_px is None:
        tracker.state = MotionState.NO_HAND
        clear(tracker)
        return tracker.state
    tip_px = np.asarray(tip_px, dtype=float)
    if tracker.state != MotionState.DRAWING:
        if not shape_ok:
            tracker.state = MotionState.SHAPING
            return tracker.state
        tracker.state = MotionState.DRAWING
        tracker.shape_lost_s = None
        place_guide(tracker, time_s, tip_px, palm_px)
    # The hand turns while drawing, so the shape may slip briefly without ending the stroke.
    if shape_ok:
        tracker.shape_lost_s = None
    elif tracker.shape_lost_s is None:
        tracker.shape_lost_s = time_s
    elif time_s - tracker.shape_lost_s > config.MOTION_SHAPE_GRACE_S:
        tracker.state = MotionState.SHAPING
        clear(tracker)
        return tracker.state
    tracker.times.append(time_s)
    tracker.points.append(tip_px)
    tracker.palms.append(palm_px)
    while time_s - tracker.times[0] > config.MOTION_WINDOW_S:
        tracker.times.pop(0)
        tracker.points.pop(0)
        tracker.palms.pop(0)
    follow_guide(tracker, time_s, tip_px, palm_px, is_left)
    if tracker.reached == len(tracker.motion.checkpoints) or found_path(tracker, is_left):
        tracker.state = MotionState.DONE
    return tracker.state


def follow_guide(tracker, time_s, tip_px, palm_px, is_left):
    """Count checkpoints as the fingertip passes them, and move the guide to a fingertip that waits elsewhere."""
    radius_px = config.CHECKPOINT_RADIUS_PALMS * tracker.anchor_palm_px
    if np.linalg.norm(tip_px - checkpoint_px(tracker, tracker.reached, is_left)) <= radius_px:
        tracker.reached += 1
        tracker.progress_s = time_s
    elif tracker.reached == 0 and is_resting(tracker):
        place_guide(tracker, time_s, tip_px, palm_px)
    elif time_s - tracker.progress_s > config.CHECKPOINT_STALL_S:
        place_guide(tracker, time_s, tip_px, palm_px)


def is_resting(tracker):
    """True when the fingertip has stayed in one small spot over the last few results."""
    recent = np.asarray(tracker.points[-config.GUIDE_REST_POINTS:])
    return len(recent) == config.GUIDE_REST_POINTS and extent(recent) <= config.GUIDE_REST_PALMS * tracker.palms[-1]


def found_path(tracker, is_left):
    """True when some recent stretch of the stroke has the letter's path shape and is big enough."""
    if len(tracker.points) < config.MOTION_MIN_POINTS:
        return False
    points = smooth(np.asarray(tracker.points))
    min_extent_px = config.MOTION_MIN_EXTENT_PALMS * float(np.median(tracker.palms))
    template = prepare(oriented_path(tracker.motion, is_left))
    for start in range(0, len(points) - config.MOTION_MIN_POINTS + 1, config.MOTION_START_STEP):
        stroke = points[start:]
        if extent(stroke) >= min_extent_px and prepared_distance(stroke, template) <= config.MOTION_MATCH_DISTANCE:
            return True
    return False
