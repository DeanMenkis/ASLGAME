"""Tests for the match detector, sign queue, and app flow."""

import unittest

from aslgame import config
from aslgame.game import match_detector
from aslgame.game.app_flow import Action, AppState, next_state
from aslgame.game.match_detector import DetectorState, MatchDetector
from aslgame.game.sign_queue import make_queue, missing_signs

HIGH = config.MATCH_THRESHOLD + 0.01
BETWEEN = (config.MATCH_THRESHOLD + config.MATCH_RELEASE_THRESHOLD) / 2
LOW = config.MATCH_RELEASE_THRESHOLD - 0.01


class MatchDetectorTest(unittest.TestCase):
    def test_hold_confirms_once(self):
        detector = MatchDetector()
        self.assertFalse(match_detector.update(detector, 0.0, HIGH))
        self.assertEqual(detector.state, DetectorState.HOLDING)
        self.assertFalse(match_detector.update(detector, config.MATCH_HOLD_S / 2, HIGH))
        self.assertAlmostEqual(detector.hold_fraction, 0.5)
        self.assertTrue(match_detector.update(detector, config.MATCH_HOLD_S, HIGH))
        self.assertEqual(detector.state, DetectorState.MATCHED)
        self.assertFalse(match_detector.update(detector, config.MATCH_HOLD_S * 2, HIGH))

    def test_dip_above_release_keeps_hold(self):
        detector = MatchDetector()
        match_detector.update(detector, 0.0, HIGH)
        match_detector.update(detector, 0.1, BETWEEN)
        self.assertEqual(detector.state, DetectorState.HOLDING)

    def test_drop_below_release_restarts(self):
        detector = MatchDetector()
        match_detector.update(detector, 0.0, HIGH)
        match_detector.update(detector, 0.1, LOW)
        self.assertEqual(detector.state, DetectorState.SEARCHING)
        self.assertEqual(detector.hold_fraction, 0.0)

    def test_between_does_not_start_hold(self):
        detector = MatchDetector()
        match_detector.update(detector, 0.0, BETWEEN)
        self.assertEqual(detector.state, DetectorState.SEARCHING)

    def test_lost_hand(self):
        detector = MatchDetector()
        match_detector.update(detector, 0.0, HIGH)
        match_detector.update(detector, 0.1, None)
        self.assertEqual(detector.state, DetectorState.NO_HAND)
        self.assertEqual(detector.hold_fraction, 0.0)


class SignQueueTest(unittest.TestCase):
    def test_sentence_skips_spaces(self):
        queue = make_queue("  good   day ")
        self.assertEqual(queue.text, "GOOD DAY")
        signs = []
        while not queue.is_done():
            signs.append(queue.current_sign())
            queue.advance()
        self.assertEqual("".join(signs), "GOODDAY")
        self.assertIsNone(queue.current_sign())

    def test_missing_signs(self):
        self.assertEqual(missing_signs("Cab", {"A", "B"}), ["C"])
        self.assertEqual(missing_signs("a b", {"A", "B"}), [])


class AppFlowTest(unittest.TestCase):
    def test_learn_round_trip(self):
        state = AppState.BOOT
        for action, expected in [
            (Action.READY, AppState.MENU),
            (Action.START_LEARN, AppState.LEARN),
            (Action.PAUSE, AppState.PAUSED),
            (Action.RESUME, AppState.LEARN),
            (Action.PAUSE, AppState.PAUSED),
            (Action.TO_MENU, AppState.MENU),
        ]:
            state = next_state(state, action)
            self.assertEqual(state, expected)

    def test_unknown_action_keeps_state(self):
        self.assertEqual(next_state(AppState.MENU, Action.RESUME), AppState.MENU)

    def test_quit_from_anywhere(self):
        for state in AppState:
            self.assertEqual(next_state(state, Action.QUIT), AppState.QUIT)


if __name__ == "__main__":
    unittest.main()
