"""Tests for normalization, matching, and sign storage. Needs no camera or window."""

import tempfile
import unittest
from pathlib import Path

import numpy as np

from aslgame import config
from aslgame.matching import matcher
from aslgame.matching.normalize import normalize, palm_size, place_on
from aslgame.signs import load_signs, make_sign, save_sign

RNG = np.random.default_rng(0)


def random_hand():
    return RNG.uniform(0, 100, size=(21, 3)).astype(np.float32)


class NormalizeTest(unittest.TestCase):
    def test_ignores_position_and_size(self):
        hand = random_hand()
        moved = hand * 3.0 + np.array([50, -20, 7], dtype=np.float32)
        np.testing.assert_allclose(normalize(hand, False), normalize(moved, False), atol=1e-4)

    def test_wrist_at_origin_and_unit_palm(self):
        normalized = normalize(random_hand(), False)
        np.testing.assert_allclose(normalized[0], 0, atol=1e-6)
        self.assertAlmostEqual(palm_size(normalized), 1.0, places=5)

    def test_left_hand_mirrors_right(self):
        right = random_hand()
        left = right * np.array([-1, 1, 1], dtype=np.float32)
        np.testing.assert_allclose(normalize(right, False), normalize(left, True), atol=1e-4)

    def test_place_on_inverts_normalize(self):
        for is_left in (False, True):
            hand = random_hand()
            np.testing.assert_allclose(place_on(normalize(hand, is_left), hand, is_left), hand, atol=1e-3)


class MatcherTest(unittest.TestCase):
    def test_exact_match_scores_one(self):
        hand = normalize(random_hand(), False)
        self.assertAlmostEqual(matcher.score(hand, hand[None]), 1.0)

    def test_far_hand_scores_zero(self):
        hand = normalize(random_hand(), False)
        far = hand + config.MATCH_ZERO_SCORE_DISTANCE * 2
        self.assertEqual(matcher.score(far, hand[None]), 0.0)

    def test_uses_closest_sample(self):
        hand = normalize(random_hand(), False)
        samples = np.stack([hand + 5, hand])
        self.assertAlmostEqual(matcher.score(hand, samples), 1.0)

    def test_best_match_picks_closest_sign(self):
        a, b = normalize(random_hand(), False), normalize(random_hand(), False)
        signs = {"A": make_sign("A", [a]), "B": make_sign("B", [b])}
        self.assertEqual(matcher.best_match(a, signs)[0], "A")
        self.assertEqual(matcher.best_match(b, signs)[0], "B")

    def test_target_score_rejects_clearly_better_rival(self):
        a, b = normalize(random_hand(), False), normalize(random_hand(), False)
        signs = {"A": make_sign("A", [a]), "B": make_sign("B", [b])}
        self.assertEqual(matcher.target_score(a, signs["B"], signs), 0.0)
        self.assertAlmostEqual(matcher.target_score(a, signs["A"], signs), 1.0)

    def test_best_match_without_signs(self):
        self.assertEqual(matcher.best_match(np.zeros((21, 3)), {}), (None, 0.0))


class SignsTest(unittest.TestCase):
    def test_outline_always_matches(self):
        far_apart = [normalize(random_hand(), False) for _ in range(3)]
        sign = make_sign("A", far_apart)
        self.assertAlmostEqual(matcher.score(sign.outline, sign.samples), 1.0)

    def test_save_appends_and_loads(self):
        with tempfile.TemporaryDirectory() as directory:
            signs_dir = Path(directory)
            hand = normalize(random_hand(), False)
            save_sign(signs_dir, "A", [hand])
            self.assertEqual(save_sign(signs_dir, "A", [hand, hand]), 3)
            sign = load_signs(signs_dir)["A"]
            self.assertEqual(sign.samples.shape, (4, 21, 3))  # three saved plus the outline
            np.testing.assert_allclose(sign.outline, hand, atol=1e-3)


if __name__ == "__main__":
    unittest.main()
