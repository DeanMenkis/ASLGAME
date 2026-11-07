"""Tests for the game clock and rhythm session. Needs no camera or window."""

import unittest

from aslgame import config
from aslgame.game import rhythm
from aslgame.game.clock import GameClock
from aslgame.game.rhythm import Judgement, Note, NoteState, RhythmSession

HIGH = config.MATCH_THRESHOLD + 0.1
STEP_S = 1 / 60


def run(session, until_s, score_at):
    """Step the session at 60 fps. score_at(game_s, target_note) gives the score fed in."""
    game_s = 0.0
    while game_s <= until_s and not session.is_finished():
        rhythm.update(session, game_s, score_at(game_s, session.target()))
        game_s += STEP_S
    return session


def sign_on_beat(game_s, note):
    """A perfect player: the right sign from slightly before each note is due."""
    return HIGH if note is not None and game_s >= note.due_s - config.RHYTHM_HOLD_S else 0.0


class ClockTest(unittest.TestCase):
    def test_pause_excludes_paused_time(self):
        clock = GameClock(started_s=10.0)
        self.assertEqual(clock.time(12.0), 2.0)
        clock.pause(12.0)
        self.assertEqual(clock.time(20.0), 2.0)
        clock.resume(20.0)
        self.assertEqual(clock.time(21.0), 3.0)


class NoteTest(unittest.TestCase):
    def test_states_in_order(self):
        note = Note("A", due_s=5.0, approach_s=2.0)
        rhythm.update_note(note, 2.0, False)
        self.assertEqual(note.state, NoteState.WAITING)
        rhythm.update_note(note, 3.5, False)
        self.assertEqual(note.state, NoteState.APPROACHING)
        rhythm.update_note(note, 4.9, False)
        self.assertEqual(note.state, NoteState.HITTABLE)
        rhythm.update_note(note, 5.05, True)
        self.assertEqual((note.state, note.judgement), (NoteState.HIT, Judgement.PERFECT))
        rhythm.update_note(note, 5.05 + config.FEEDBACK_S, False)
        self.assertEqual(note.state, NoteState.DONE)

    def test_miss_after_window(self):
        note = Note("A", due_s=5.0, approach_s=2.0)
        for game_s in (4.0, 4.9, 5.0 + config.HIT_WINDOW_S + 0.01):
            rhythm.update_note(note, game_s, False)
        self.assertEqual((note.state, note.judgement), (NoteState.MISSED, Judgement.MISS))

    def test_match_before_window_waits(self):
        note = Note("A", due_s=5.0, approach_s=2.0)
        rhythm.update_note(note, 3.5, True)
        self.assertEqual(note.state, NoteState.APPROACHING)

    def test_judge_windows(self):
        self.assertEqual(rhythm.judge(-0.1), Judgement.PERFECT)
        self.assertEqual(rhythm.judge(0.25), Judgement.GOOD)
        self.assertEqual(rhythm.judge(-0.45), Judgement.OK)


class SessionTest(unittest.TestCase):
    def test_perfect_player_hits_everything_and_speeds_up(self):
        session = run(RhythmSession(list("ABCDEFGH")), 60.0, sign_on_beat)
        self.assertTrue(session.is_finished())
        judgements = [judgement for _, judgement in session.results]
        self.assertEqual(len(judgements), 8)
        self.assertNotIn(Judgement.MISS, judgements)
        self.assertEqual(session.max_combo, 8)
        self.assertGreater(session.speed, 1.0)

    def test_idle_player_misses_and_slows_down(self):
        session = run(RhythmSession(list("ABCDEFGH")), 120.0, lambda game_s, note: None)
        self.assertTrue(session.is_finished())
        self.assertTrue(all(judgement == Judgement.MISS for _, judgement in session.results))
        self.assertEqual((session.combo, session.score), (0, 0))
        self.assertLess(session.speed, 1.0)

    def test_speed_stays_in_bounds(self):
        session = RhythmSession(["A"])
        for _ in range(100):
            rhythm.adapt_speed(session, 1.0)
        self.assertEqual(session.speed, config.SPEED_MAX)
        for _ in range(100):
            rhythm.adapt_speed(session, 0.0)
        self.assertEqual(session.speed, config.SPEED_MIN)

    def test_summary_lists_weakest_signs(self):
        session = RhythmSession(["A", "B"])
        session.results = [("A", Judgement.PERFECT), ("B", Judgement.MISS), ("B", Judgement.GOOD)]
        results = rhythm.summarize(session)
        self.assertEqual(results.weakest, [("B", 0.35)])
        self.assertEqual(results.counts[Judgement.MISS], 1)
        self.assertAlmostEqual(results.accuracy, 1.7 / 3)

    def test_beat_phase_is_zero_on_note(self):
        session = RhythmSession(list("ABC"))
        rhythm.spawn_notes(session, 100.0)
        due_s = session.due_times[1]
        self.assertAlmostEqual(session.beat_phase(due_s), 0.0)
        self.assertAlmostEqual(session.beat_phase(due_s + session.beat_s() / 2), 0.5)


if __name__ == "__main__":
    unittest.main()
