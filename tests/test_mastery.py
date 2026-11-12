"""Tests for letter mastery and the Practise deck."""

import random
import unittest

from aslgame import config
from aslgame.game import mastery
from aslgame.game.app_flow import Action, AppState, next_state
from aslgame.game.chart import Chart
from aslgame.game.mastery import Mastery
from aslgame.game.scoring import Judgement
from aslgame.game.words import ALPHABET, DECKS_BY_NAME, PRACTISE, draw_words

WEAK = "MNST"


def played_letters():
    """Most letters signed well, a few signed badly."""
    letters = {}
    mastery.record(letters, [(letter, Judgement.PERFECT) for letter in "ABCDEFGHIKLORUVWY"] * 3)
    mastery.record(letters, [(letter, Judgement.MISS) for letter in WEAK])
    return letters


class MasteryTest(unittest.TestCase):
    def test_untested_until_signed(self):
        self.assertEqual(mastery.state({}, "A"), Mastery.UNTESTED)
        self.assertEqual(mastery.need({}, "A"), config.MASTERY_UNTESTED_NEED)

    def test_two_perfects_make_a_letter_known(self):
        letters = {}
        mastery.record(letters, [("A", Judgement.PERFECT)])
        self.assertEqual(mastery.state(letters, "A"), Mastery.WEAK)
        mastery.record(letters, [("A", Judgement.PERFECT)])
        self.assertEqual(mastery.state(letters, "A"), Mastery.KNOWN)
        self.assertEqual(mastery.need(letters, "A"), 0.0)
        self.assertEqual(letters["A"]["seen"], 2)

    def test_a_miss_makes_a_known_letter_weak_again(self):
        letters = {}
        mastery.record(letters, [("A", Judgement.PERFECT)] * 3 + [("A", Judgement.MISS)])
        self.assertEqual(mastery.state(letters, "A"), Mastery.WEAK)

    def test_slow_signs_never_become_known(self):
        letters = {}
        mastery.record(letters, [("A", Judgement.OK)] * 20)
        self.assertEqual(mastery.state(letters, "A"), Mastery.WEAK)

    def test_weak_letters_weakest_first(self):
        letters = played_letters()
        mastery.record(letters, [("P", Judgement.GOOD)])
        self.assertEqual(mastery.weak_letters(letters), list(WEAK) + ["P"])
        self.assertEqual(mastery.known_count(letters), 17)

    def test_clean_drops_damaged_entries(self):
        saved = {"A": {"seen": 2, "score": 0.8}, "B": "broken", "C": {"seen": "x", "score": 1}, "D": {"score": 0.5}}
        self.assertEqual(mastery.clean(saved), {"A": {"seen": 2, "score": 0.8}})


class PractiseDeckTest(unittest.TestCase):
    def weak_share(self, deck, letters):
        signed = weak = 0
        for seed in range(100):
            for word in draw_words(deck, 0, 40, random.Random(seed), set(ALPHABET), lambda letter: mastery.need(letters, letter)):
                signed += len(word)
                weak += sum(letter in WEAK for letter in word)
        return weak / signed

    def test_weak_letters_come_up_more(self):
        letters = played_letters()
        self.assertGreater(self.weak_share(PRACTISE, letters), 1.5 * self.weak_share(DECKS_BY_NAME["everything"], letters))

    def test_no_history_still_deals_words(self):
        words = draw_words(PRACTISE, 0, 40, random.Random(1), set(ALPHABET), lambda letter: mastery.need({}, letter))
        self.assertGreaterEqual(sum(len(word) for word in words), 40)

    def test_no_word_twice_in_a_batch(self):
        letters = played_letters()
        words = draw_words(PRACTISE, 0, 40, random.Random(1), set(ALPHABET), lambda letter: mastery.need(letters, letter))
        self.assertEqual(len(words), len(set(words)))


class PractiseRunTest(unittest.TestCase):
    def test_song_keeps_its_music_and_changes_deck(self):
        chart = Chart("bouncer", "Bouncer", "bouncer.mp3", 128.0, 0.5, "party")
        item, level, length_s, key = mastery.practise_run((chart, 0, 60, "Music/bouncer/Easy/60"))
        self.assertEqual((item.name, item.media, item.deck), ("bouncer", "bouncer.mp3", "practise"))
        self.assertEqual(key, "Music/bouncer+practise/Easy/60")
        self.assertEqual(mastery.practise_run((item, level, length_s, key)), (item, level, length_s, key))

    def test_practise_from_results_replays_the_mode(self):
        self.assertEqual(next_state(AppState.RESULTS, Action.PRACTISE, AppState.MUSIC), AppState.MUSIC)
        self.assertEqual(next_state(AppState.MENU, Action.PRACTISE, AppState.MUSIC), AppState.MENU)


if __name__ == "__main__":
    unittest.main()
