"""Rush mode: no beat. Sign each letter as fast as you can before the clock runs out."""

from dataclasses import dataclass, field

from aslgame import config
from aslgame.game import match_detector, scoring
from aslgame.game.match_detector import MatchDetector
from aslgame.game.motion import MOTION_SIGNS
from aslgame.game.scoring import EventKind, Judgement, Tally


@dataclass
class RushSession:
    signs: list
    word_ends: frozenset
    length_s: float  # grows when a word is cleared
    fuse_s: float  # how long one sign may take before it is missed
    tally: Tally = field(default_factory=Tally)
    index: int = 0
    sign_started_s: float = config.RUSH_LEAD_IN_S
    bonus_s: float = 0.0
    detector: MatchDetector = field(default_factory=lambda: MatchDetector(hold_s=config.RHYTHM_HOLD_S))
    finished: bool = False

    def target(self):
        return None if self.finished else self.signs[self.index]

    def is_finished(self):
        return self.finished

    def time_left_s(self, game_s):
        return max(0.0, self.length_s - game_s)

    def allowance(self):
        """How much longer than a still letter the current sign may take."""
        return config.RUSH_MOTION_FACTOR if self.signs[self.index] in MOTION_SIGNS else 1.0

    def fuse_fraction(self, game_s):
        """1.0 when the sign appears, 0.0 when its fuse has burned down."""
        used = (game_s - self.sign_started_s) / (self.fuse_s * self.allowance())
        return min(1.0, max(0.0, 1.0 - used))


def judge(took_s, allowance=1.0):
    if took_s <= config.RUSH_PERFECT_S * allowance:
        return Judgement.PERFECT
    if took_s <= config.RUSH_GOOD_S * allowance:
        return Judgement.GOOD
    return Judgement.OK


def update(session, game_s, target_score):
    """Advance the session. target_score is the current sign's score, or None when no hand is seen."""
    if session.finished:
        return
    if game_s >= session.length_s:
        session.finished = True
        return
    if game_s < session.sign_started_s:
        return
    took_s = game_s - session.sign_started_s
    if match_detector.update(session.detector, game_s, target_score):
        advance(session, game_s, judge(took_s, session.allowance()))
    elif session.fuse_fraction(game_s) <= 0.0:
        advance(session, game_s, Judgement.MISS)


def advance(session, game_s, judgement):
    cleared = session.tally.words_cleared
    scoring.record(session.tally, session.signs[session.index], judgement, session.index in session.word_ends)
    if session.tally.words_cleared > cleared:
        session.length_s += config.RUSH_WORD_BONUS_S
        session.bonus_s += config.RUSH_WORD_BONUS_S
    session.detector = MatchDetector(hold_s=config.RHYTHM_HOLD_S)
    session.index += 1
    session.sign_started_s = game_s
    session.finished = session.index >= len(session.signs)


def signs_for(length_s):
    """Enough signs that even the fastest run never reaches the end."""
    return int(length_s / config.RUSH_FASTEST_SIGN_S)
