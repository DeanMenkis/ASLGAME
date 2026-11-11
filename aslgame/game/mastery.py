"""Letter mastery: how well each letter has been signed across runs, and which letters need practice."""

from dataclasses import replace
from enum import Enum, auto

from aslgame import config
from aslgame.game.chart import Chart
from aslgame.game.scoring import ACCURACY
from aslgame.game.words import PRACTISE


class Mastery(Enum):
    UNTESTED = auto()
    WEAK = auto()
    KNOWN = auto()


def clean(saved):
    """Keep only well-formed entries, so a damaged file never stops the game."""
    return {letter: {"seen": int(entry["seen"]), "score": float(entry["score"])}
            for letter, entry in saved.items()
            if isinstance(entry, dict) and isinstance(entry.get("seen"), int) and isinstance(entry.get("score"), (int, float))}


def record(letters, results):
    """Fold a run's (sign, judgement) results into the saved scores. Recent signs count most."""
    for sign, judgement in results:
        entry = letters.setdefault(sign, {"seen": 0, "score": config.MASTERY_START})
        entry["seen"] += 1
        entry["score"] = round(entry["score"] + config.MASTERY_RATE * (ACCURACY[judgement] - entry["score"]), 4)


def state(letters, letter):
    entry = letters.get(letter)
    if entry is None:
        return Mastery.UNTESTED
    return Mastery.KNOWN if entry["score"] >= config.MASTERY_KNOWN else Mastery.WEAK


def weak_letters(letters):
    """Tested letters that are not yet known, weakest first."""
    weak = [letter for letter in letters if state(letters, letter) == Mastery.WEAK]
    return sorted(weak, key=lambda letter: (letters[letter]["score"], letter))


def known_count(letters):
    return sum(state(letters, letter) == Mastery.KNOWN for letter in letters)


def need(letters, letter):
    """How much a letter needs practice, from 0 to 1. Untested letters sit between known and weak."""
    current = state(letters, letter)
    if current == Mastery.UNTESTED:
        return config.MASTERY_UNTESTED_NEED
    return 0.0 if current == Mastery.KNOWN else 1.0 - letters[letter]["score"]


def practise_run(played):
    """The same mode, level, and length as a finished run, on the Practise deck, with its own best score."""
    item, level, length_s, key = played
    mode, name, rest = key.split("/", 2)
    if isinstance(item, Chart):
        if item.deck == PRACTISE.name:
            return played
        return replace(item, deck=PRACTISE.name), level, length_s, f"{mode}/{name}+{PRACTISE.name}/{rest}"
    return PRACTISE, level, length_s, f"{mode}/{PRACTISE.name}/{rest}"
