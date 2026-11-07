"""Tests for motion signs. Needs no camera or window."""

import unittest

import numpy as np

from aslgame import config
from aslgame.game import motion
from aslgame.game.motion import MOTION_SIGNS, MotionState, MotionTracker

STEP_S = 1 / 30


def draw(tracker, path, is_left=False, shape_ok=True, start_s=0.0, points=30):
    """Feed a stroke along path at 30 results a second. Returns the final state."""
    state = tracker.state
    for index, point in enumerate(motion.resample(np.asarray(path, dtype=float), points)):
        state = motion.update(tracker, start_s + index * STEP_S, shape_ok, point + (2.0, 3.0), is_left)
    return state


class MotionTest(unittest.TestCase):
    def test_z_is_recognized(self):
        self.assertEqual(draw(MotionTracker(MOTION_SIGNS["Z"]), MOTION_SIGNS["Z"].path), MotionState.DONE)

    def test_j_is_recognized(self):
        self.assertEqual(draw(MotionTracker(MOTION_SIGNS["J"]), MOTION_SIGNS["J"].path), MotionState.DONE)

    def test_left_hand_draws_mirrored(self):
        mirrored = MOTION_SIGNS["Z"].path * motion.MIRROR_X
        self.assertEqual(draw(MotionTracker(MOTION_SIGNS["Z"]), mirrored, is_left=True), MotionState.DONE)
        self.assertNotEqual(draw(MotionTracker(MOTION_SIGNS["Z"]), mirrored, is_left=False), MotionState.DONE)

    def test_wrong_strokes_fail(self):
        for path in ([(0, 0), (1.2, 0)], MOTION_SIGNS["Z"].path[::-1], [(0, 0), (0, 1.4)]):
            for name in ("Z", "J"):
                self.assertNotEqual(draw(MotionTracker(MOTION_SIGNS[name]), path), MotionState.DONE, (name, path))

    def test_tiny_stroke_fails(self):
        small = MOTION_SIGNS["Z"].path * (config.MOTION_MIN_EXTENT_PALMS / 3)
        self.assertNotEqual(draw(MotionTracker(MOTION_SIGNS["Z"]), small), MotionState.DONE)

    def test_needs_the_shape(self):
        tracker = MotionTracker(MOTION_SIGNS["Z"])
        self.assertEqual(draw(tracker, MOTION_SIGNS["Z"].path, shape_ok=False), MotionState.SHAPING)

    def test_lost_hand_clears_the_stroke(self):
        tracker = MotionTracker(MOTION_SIGNS["Z"])
        draw(tracker, MOTION_SIGNS["Z"].path[:2])
        self.assertEqual(motion.update(tracker, 5.0, True, None, False), MotionState.NO_HAND)
        self.assertEqual(tracker.points, [])

    def test_stroke_after_wandering_still_counts(self):
        tracker = MotionTracker(MOTION_SIGNS["Z"])
        draw(tracker, [(0, 0), (-0.5, 0.4), (0.3, -0.2)], points=12)
        self.assertEqual(draw(tracker, MOTION_SIGNS["Z"].path, start_s=0.5), MotionState.DONE)


if __name__ == "__main__":
    unittest.main()
