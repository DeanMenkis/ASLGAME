"""Tests for the game clock, rhythm session, scoring, and rush. Needs no camera or window."""

import unittest

from aslgame import config
from aslgame.game import rhythm, rush, scoring
from aslgame.game.clock import GameClock
from aslgame.game.rhythm import Note, NoteState, RhythmSession
from aslgame.game.scoring import EventKind, Judgement, Tally

HIGH = config.MATCH_THRESHOLD + 0.1
STEP_S = 1 / 60


def run(session, until_s, score_at):
    """Step the session at 60 fps. score_at(game_s, target_note) gives the score fed in."""
    game_s = 0.0
    while game_s <= until_s and not session.is_finished():
        rhythm.update(session, game_s, score_at(game_s, session.target()))
        game_s += STEP_S
    return session


def always_right(game_s, note):
    return HIGH if note is not None else None


class ClockTest(unittest.TestCase):
    def test_pause_excludes_paused_time(self):
        clock = GameClock(started_s=10.0)
        self.assertEqual(clock.time(12.0), 2.0)
        clock.pause(12.0)
        self.assertEqual(clock.time(20.0), 2.0)
        clock.resume(20.0)
        self.assertEqual(clock.time(21.0), 3.0)


class NoteTest(unittest.TestCase):
    def test_early_sign_lands_on_the_beat_as_perfect(self):
        note = Note("A", due_s=5.0, approach_s=2.0)
        rhythm.update_note(note, 3.5)
        note.locked_s = 3.6
        rhythm.update_note(note, 4.9)
        self.assertEqual(note.state, NoteState.APPROACHING)
        rhythm.update_note(note, 5.0)
        self.assertEqual((note.state, note.judgement), (NoteState.HIT, Judgement.PERFECT))

    def test_miss_after_window(self):
        note = Note("A", due_s=5.0, approach_s=2.0)
        for game_s in (4.0, 5.0, 5.0 + config.HIT_WINDOW_S + 0.01):
            rhythm.update_note(note, game_s)
        self.assertEqual((note.state, note.judgement), (NoteState.MISSED, Judgement.MISS))

    def test_late_judgements(self):
        window = config.HIT_WINDOW_S
        self.assertEqual(rhythm.judge(-1.0), Judgement.PERFECT)
        self.assertEqual(rhythm.judge(window * 0.2), Judgement.PERFECT)
        self.assertEqual(rhythm.judge(window * 0.5), Judgement.GOOD)
        self.assertEqual(rhythm.judge(window * 0.9), Judgement.OK)


class SessionTest(unittest.TestCase):
    def test_ready_player_gets_all_perfects_and_an_s(self):
        session = run(RhythmSession(list("ABCDEFGH")), 60.0, always_right)
        self.assertTrue(session.is_finished())
        self.assertEqual([j for _, j in session.tally.results], [Judgement.PERFECT] * 8)
        self.assertEqual(scoring.summarize(session.tally).grade, "S")
        self.assertGreater(session.speed, 1.0)

    def test_idle_player_misses_and_gets_a_d(self):
        session = run(RhythmSession(list("ABCDEFGH")), 120.0, lambda game_s, note: None)
        self.assertTrue(all(j == Judgement.MISS for _, j in session.tally.results))
        self.assertEqual(scoring.summarize(session.tally).grade, "D")
        self.assertLess(session.speed, 1.0)

    def test_fast_signer_spells_ahead(self):
        session = RhythmSession(list("ABCD"), beats_per_note=1)
        rhythm.update(session, 0.0, None)
        rhythm.update(session, 0.1, HIGH)
        rhythm.update(session, 0.2, HIGH)
        locked = [note for note in session.notes if note.locked_s is not None]
        self.assertGreaterEqual(len(locked), 1)

    def test_run_stops_after_last_due(self):
        session = RhythmSession(list("AB") * 50, frozenset(range(1, 100, 2)), last_due_s=10.0)
        run(session, 200.0, always_right)
        self.assertTrue(session.is_finished())
        self.assertLess(len(session.tally.results), 100)
        self.assertEqual(len(session.tally.results) % 2, 0)  # never stops mid word

    def test_drawn_letters_get_extra_time(self):
        session = RhythmSession(["A", "Z", "B"], beats_per_note=1)
        rhythm.spawn_notes(session, 100.0)
        gaps = [b.due_s - a.due_s for a, b in zip(session.notes, session.notes[1:])]
        self.assertGreater(gaps[0], gaps[1])

    def test_speed_stays_in_bounds(self):
        session = RhythmSession(["A"])
        for _ in range(100):
            rhythm.adapt_speed(session, 1.0)
        self.assertEqual(session.speed, config.SPEED_MAX)
        for _ in range(100):
            rhythm.adapt_speed(session, 0.0)
        self.assertEqual(session.speed, config.SPEED_MIN)


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


class RushTest(unittest.TestCase):
    def test_quick_signs_are_perfect_and_the_clock_ends_it(self):
        session = rush.RushSession(list("AB") * 200, frozenset(range(1, 400, 2)), 5.0, 3.0)
        game_s = 0.0
        while not session.is_finished():
            rush.update(session, game_s, HIGH)
            game_s += STEP_S
        self.assertGreater(len(session.tally.results), 10)
        self.assertTrue(all(j == Judgement.PERFECT for _, j in session.tally.results))
        self.assertGreater(session.bonus_s, 0)

    def test_fuse_burns_out_to_a_miss(self):
        session = rush.RushSession(list("AB"), frozenset({1}), 30.0, 1.0)
        game_s = 0.0
        while not session.tally.results:
            rush.update(session, game_s, None)
            game_s += STEP_S
        self.assertEqual(session.tally.results[0][1], Judgement.MISS)


if __name__ == "__main__":
    unittest.main()
