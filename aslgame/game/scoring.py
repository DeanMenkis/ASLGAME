"""Scoring shared by the timed modes: judgements, combo, the multiplier and its tiers, word bonuses, and grades."""

from dataclasses import dataclass, field
from enum import Enum, auto

from aslgame import config


class Judgement(Enum):
    PERFECT = auto()
    GOOD = auto()
    OK = auto()
    MISS = auto()


POINTS = {Judgement.PERFECT: 300, Judgement.GOOD: 100, Judgement.OK: 50, Judgement.MISS: 0}
ACCURACY = {Judgement.PERFECT: 1.0, Judgement.GOOD: 0.8, Judgement.OK: 0.5, Judgement.MISS: 0.0}


class EventKind(Enum):
    LOCK = auto()  # a sign was recognized ahead of its beat
    HIT = auto()
    MISS = auto()
    TIER_UP = auto()  # the multiplier crossed a whole number
    BREAK = auto()  # a miss threw away a multiplier of x2 or more
    WORD = auto()  # a whole word was signed without a miss


@dataclass(frozen=True)
class Event:
    kind: EventKind
    judgement: Judgement | None = None
    points: int = 0
    multiplier: float = 1.0
    combo: int = 0
    tier: int = 1
    word: str = ""
    on_beat: bool = False


@dataclass
class Tally:
    """The running score of one run. Screens drain events to play sounds and effects."""

    score: int = 0
    combo: int = 0
    max_combo: int = 0
    perfect_streak: int = 0
    multiplier: float = 1.0
    max_multiplier: float = 1.0
    last_points: int = 0
    words_cleared: int = 0
    clean_words: list = field(default_factory=list)  # every word signed without a miss, in order
    word: str = ""  # letters of the current word so far
    word_clean: bool = True
    results: list = field(default_factory=list)  # (sign, judgement) of every resolved sign
    events: list = field(default_factory=list)


def tier(multiplier_value):
    return int(multiplier_value)


def multiplier(tally, speed=1.0):
    """Grows with combo, with a run of Perfects, and with speed: bigger, faster, steadier play pays more."""
    combo_part = min(tally.combo, config.COMBO_CAP) * config.COMBO_BONUS
    streak_part = min(tally.perfect_streak * config.PERFECT_STREAK_BONUS, config.PERFECT_STREAK_CAP)
    speed_part = max(0.0, speed - 1.0) * config.SPEED_BONUS
    return min(config.MULTIPLIER_MAX, round(1.0 + combo_part + streak_part + speed_part, 1))


def record(tally, sign, judgement, ends_word=False, speed=1.0, bonus=1.0):
    """Score one resolved sign. The only place a tally changes."""
    tally.results.append((sign, judgement))
    before = tally.multiplier
    if judgement == Judgement.MISS:
        tally.combo = tally.perfect_streak = 0
        tally.word_clean = False
    else:
        tally.combo += 1
        tally.max_combo = max(tally.max_combo, tally.combo)
        tally.perfect_streak = tally.perfect_streak + 1 if judgement == Judgement.PERFECT else 0
    tally.multiplier = multiplier(tally, speed)
    tally.max_multiplier = max(tally.max_multiplier, tally.multiplier)
    tally.last_points = int(POINTS[judgement] * tally.multiplier * bonus)
    tally.score += tally.last_points
    kind = EventKind.MISS if judgement == Judgement.MISS else EventKind.HIT
    tally.events.append(Event(kind, judgement, tally.last_points, tally.multiplier, tally.combo, tier(tally.multiplier),
                              on_beat=bonus > 1.0))
    if tier(tally.multiplier) > tier(before):
        tally.events.append(Event(EventKind.TIER_UP, multiplier=tally.multiplier, tier=tier(tally.multiplier)))
    elif judgement == Judgement.MISS and tier(before) >= 2:
        tally.events.append(Event(EventKind.BREAK, multiplier=before, tier=tier(before)))
    tally.word += sign
    if ends_word:
        finish_word(tally)


def finish_word(tally):
    """A word signed without a miss pays a bonus for every letter in it."""
    if tally.word_clean and len(tally.word) >= config.WORD_BONUS_MIN_SIGNS:
        points = int(config.WORD_BONUS_PER_SIGN * len(tally.word) * tally.multiplier)
        tally.score += points
        tally.words_cleared += 1
        tally.clean_words.append(tally.word)
        tally.events.append(Event(EventKind.WORD, points=points, multiplier=tally.multiplier, word=tally.word))
    tally.word = ""
    tally.word_clean = True


def grade(accuracy):
    # Judged on the percentage shown, so 88% on screen is never a grade below what 88% earns.
    accuracy = round(accuracy, 2)
    for letter, minimum in config.GRADES:
        if accuracy >= minimum:
            return letter
    return config.GRADES[-1][0]


@dataclass(frozen=True)
class Results:
    score: int
    max_combo: int
    max_multiplier: float
    words_cleared: int
    accuracy: float
    counts: dict
    weakest: list  # (sign, accuracy), weakest first
    grade: str
    words: tuple = ()  # the words signed without a miss, in order


def summarize(tally):
    counts = {judgement: 0 for judgement in Judgement}
    per_sign = {}
    for sign, judgement in tally.results:
        counts[judgement] += 1
        per_sign.setdefault(sign, []).append(ACCURACY[judgement])
    accuracy = sum(ACCURACY[j] for _, j in tally.results) / len(tally.results) if tally.results else 0.0
    sign_accuracy = sorted(((sign, sum(v) / len(v)) for sign, v in per_sign.items()), key=lambda item: item[1])
    weakest = [item for item in sign_accuracy if item[1] < 1.0][: config.RESULTS_WEAKEST_COUNT]
    return Results(tally.score, tally.max_combo, tally.max_multiplier, tally.words_cleared, accuracy, counts, weakest,
                   grade(accuracy), tuple(tally.clean_words))
