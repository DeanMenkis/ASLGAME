"""Tests for the camera print and the clean words a run keeps."""

import unittest

import numpy as np

from aslgame import theme
from aslgame.capture.print_look import Look, Printer
from aslgame.game import scoring
from aslgame.game.scoring import Judgement

SIZE_PX = (64, 48)


def picture(color):
    return np.full((SIZE_PX[1], SIZE_PX[0], 3), color, np.uint8)


class PrinterTest(unittest.TestCase):
    def setUp(self):
        self.printer = Printer(SIZE_PX)

    def test_keeps_the_frame_size(self):
        printed = self.printer.print(picture((120, 90, 70)), Look())
        self.assertEqual(printed.shape, (SIZE_PX[1], SIZE_PX[0], 3))
        self.assertEqual(printed.dtype, np.uint8)

    def test_white_prints_as_bare_paper(self):
        printed = self.printer.print(picture((255, 255, 255)), Look())
        self.assertTrue(np.abs(printed.astype(int) - np.array(theme.PAPER)).max() <= 1)

    def test_shadows_print_blue_and_skin_prints_red(self):
        shadow = self.printer.print(picture((20, 20, 20)), Look()).mean(axis=(0, 1))
        skin = self.printer.print(picture((220, 160, 130)), Look()).mean(axis=(0, 1))
        self.assertGreater(shadow[2], shadow[0])
        self.assertGreater(skin[0], skin[2])

    def test_heat_adds_yellow(self):
        cold = self.printer.print(picture((200, 190, 150)), Look(0.0)).mean(axis=(0, 1))
        hot = self.printer.print(picture((200, 190, 150)), Look(1.0)).mean(axis=(0, 1))
        self.assertLess(hot[2], cold[2] - 10)

    def test_slip_moves_the_red_plate(self):
        frame = picture((40, 40, 40))
        frame[:, 20:30] = (230, 150, 120)
        registered = self.printer.print(frame, Look(0.0, 0.0))
        slipped = self.printer.print(frame, Look(0.0, 1.0))
        self.assertFalse(np.array_equal(registered, slipped))


class CleanWordsTest(unittest.TestCase):
    def test_only_words_without_a_miss_are_kept(self):
        tally = scoring.Tally()
        for word, miss_at in (("HI", None), ("NO", 0), ("YES", None)):
            for index, letter in enumerate(word):
                judgement = Judgement.MISS if index == miss_at else Judgement.PERFECT
                scoring.record(tally, letter, judgement, index == len(word) - 1)
        self.assertEqual(scoring.summarize(tally).words, ("HI", "YES"))


if __name__ == "__main__":
    unittest.main()
