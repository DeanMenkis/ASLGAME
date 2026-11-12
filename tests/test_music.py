"""Tests for the game clock, the music session, and scoring. Needs no camera or window."""

import unittest

from aslgame import config
from aslgame.game import music, scoring
from aslgame.game.chart import Chart
from aslgame.game.clock import GameClock
from aslgame.game.scoring import EventKind, Judgement, Tally

HIGH = config.MATCH_THRESHOLD + 0.1
STEP_S = 1 / 60
CHART = Chart("song", "Song", "song.mp3", 120.0, 1.0, "hello")


def play(session, score_at):
    """Step the session at 60 fps until it ends. score_at(game_s) gives the score fed in."""
    game_s = 0.0
    while not session.is_finished():
        music.update(session, game_s, score_at(game_s))
        game_s += STEP_S
    return session


class ClockTest(unittest.TestCase):
    def test_pause_excludes_paused_time(self):
        clock = GameClock(started_s=10.0)
        self.assertEqual(clock.time(12.0), 2.0)
        clock.pause(12.0)
        self.assertEqual(clock.time(20.0), 2.0)
        clock.resume(20.0)
        self.assertEqual(clock.time(21.0), 3.0)


class MusicTest(unittest.TestCase):
    def test_quick_signs_are_perfect_and_the_song_ends_it(self):
        session = play(music.make_session(["AB"] * 200, CHART, 0, 5.0), lambda game_s: HIGH)
        self.assertGreater(len(session.tally.results), 10)
        self.assertTrue(all(j == Judgement.PERFECT for _, j in session.tally.results))
        self.assertEqual(scoring.summarize(session.tally).grade, "S")

    def test_idle_player_misses_every_sign(self):
        session = play(music.make_session(["AB"] * 200, CHART, 2, 10.0), lambda game_s: None)
        self.assertTrue(session.tally.results)
        self.assertTrue(all(j == Judgement.MISS for _, j in session.tally.results))
        self.assertEqual(scoring.summarize(session.tally).grade, "D")

    def test_fuse_is_counted_in_beats_and_shorter_on_harder_levels(self):
        easy = music.make_session(["AB"], CHART, 0, 30.0)
        hard = music.make_session(["AB"], CHART, 2, 30.0)
        self.assertAlmostEqual(easy.fuse_s(), config.FUSE_BEATS[0] * 0.5)
        self.assertLess(hard.fuse_s(), easy.fuse_s())

    def test_drawn_letters_get_a_longer_fuse(self):
        session = music.make_session(["ZA"], CHART, 0, 30.0)
        drawn = session.fuse_s()
        music.advance(session, 1.0, Judgement.GOOD)
        self.assertAlmostEqual(drawn, session.fuse_s() * config.MOTION_FUSE_FACTOR)

    def test_slower_signs_judge_lower(self):
        fuse_s = 2.0
        self.assertEqual(music.judge(fuse_s * 0.2, fuse_s), Judgement.PERFECT)
        self.assertEqual(music.judge(fuse_s * 0.5, fuse_s), Judgement.GOOD)
        self.assertEqual(music.judge(fuse_s * 0.9, fuse_s), Judgement.OK)

    def test_a_sign_on_the_beat_pays_more(self):
        on, off = (music.make_session(["AB"], CHART, 0, 30.0) for _ in range(2))
        music.advance(on, CHART.first_note_s + 0.5, Judgement.PERFECT)
        music.advance(off, CHART.first_note_s + 0.25, Judgement.PERFECT)
        self.assertEqual((on.on_beats, off.on_beats), (1, 0))
        self.assertGreater(on.tally.score, off.tally.score)

    def test_first_fuse_is_lit_a_beat_before_the_first_beat(self):
        session = music.make_session(["AB"], CHART, 0, 30.0)
        self.assertEqual(session.fuse_fraction(0.0), 1.0)
        music.update(session, 0.0, HIGH)
        self.assertFalse(session.tally.results)


class ScoringTest(unittest.TestCase):
    def test_multiplier_climbs_tiers_and_caps(self):
        tally = Tally()
        for _ in range(300):
            scoring.record(tally, "A", Judgement.PERFECT)
        self.assertEqual(tally.multiplier, config.MULTIPLIER_MAX)
        tiers = [e.tier for e in tally.events if e.kind == EventKind.TIER_UP]
        self.assertEqual(tiers, list(range(2, 11)))

    def test_miss_breaks_a_high_multiplier(self):
        tally = Tally()
        for _ in range(20):
            scoring.record(tally, "A", Judgement.PERFECT)
        tally.events.clear()
        scoring.record(tally, "A", Judgement.MISS)
        self.assertEqual((tally.combo, tally.multiplier), (0, 1.0))
        self.assertIn(EventKind.BREAK, [e.kind for e in tally.events])

    def test_clean_word_pays_a_bonus(self):
        clean, dirty = Tally(), Tally()
        for letter in "CAT":
            scoring.record(clean, letter, Judgement.GOOD, ends_word=letter == "T")
        for letter, judgement in zip("CAT", (Judgement.GOOD, Judgement.MISS, Judgement.GOOD)):
            scoring.record(dirty, letter, judgement, ends_word=letter == "T")
        self.assertEqual(clean.words_cleared, 1)
        self.assertEqual(dirty.words_cleared, 0)

    def test_grades_span_d_to_s(self):
        self.assertEqual([scoring.grade(a) for a in (1.0, 0.9, 0.8, 0.6, 0.1)], ["S", "A", "B", "C", "D"])

    def test_summary_lists_weakest_signs(self):
        tally = Tally()
        for sign, judgement in (("A", Judgement.PERFECT), ("B", Judgement.MISS), ("B", Judgement.GOOD)):
            scoring.record(tally, sign, judgement)
        results = scoring.summarize(tally)
        self.assertEqual(results.weakest, [("B", 0.4)])
        self.assertEqual(results.counts[Judgement.MISS], 1)


if __name__ == "__main__":
    unittest.main()
