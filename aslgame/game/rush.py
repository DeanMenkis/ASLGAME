"""Rush and Music: sign each letter as fast as you can; the next one appears the moment you land it.

Rush races a clock that clean words extend. Music races the song: fuses are counted in beats,
and a sign that lands on a beat scores an on-beat bonus.
"""

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
    bpm: float | None = None  # set in Music: fuses are in beats, and beats pay a bonus
    first_beat_s: float = 0.0
    on_beats: int = 0

    def beat_s(self):
        return 60.0 / self.bpm

    def beat_offset_s(self, game_s):
        """Distance to the nearest beat."""
        phase = ((game_s - self.first_beat_s) / self.beat_s()) % 1.0
        return min(phase, 1.0 - phase) * self.beat_s()

    def beat_phase(self, game_s):
        return ((game_s - self.first_beat_s) / self.beat_s()) % 1.0

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


def judge(took_s, allowance=1.0, fuse_s=None):
    """By speed. With a fuse (Music), the limits are shares of it, so they follow the song's tempo."""
    perfect_s, good_s = config.RUSH_PERFECT_S, config.RUSH_GOOD_S
    if fuse_s is not None:
        perfect_s, good_s = fuse_s * config.FLOW_PERFECT_FRACTION, fuse_s * config.FLOW_GOOD_FRACTION
    if took_s <= perfect_s * allowance:
        return Judgement.PERFECT
    if took_s <= good_s * allowance:
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
        fuse = session.fuse_s if session.bpm else None
        advance(session, game_s, judge(took_s, session.allowance(), fuse))
    elif session.fuse_fraction(game_s) <= 0.0:
        advance(session, game_s, Judgement.MISS)


def advance(session, game_s, judgement):
    cleared = session.tally.words_cleared
    on_beat = (session.bpm is not None and judgement != Judgement.MISS
               and session.beat_offset_s(game_s) <= config.ON_BEAT_WINDOW_S)
    session.on_beats += on_beat
    scoring.record(session.tally, session.signs[session.index], judgement, session.index in session.word_ends,
                   bonus=config.ON_BEAT_BONUS if on_beat else 1.0)
    if session.tally.words_cleared > cleared and session.bpm is None:
        session.length_s += config.RUSH_WORD_BONUS_S
        session.bonus_s += config.RUSH_WORD_BONUS_S
    session.detector = MatchDetector(hold_s=config.RHYTHM_HOLD_S)
    session.index += 1
    session.sign_started_s = game_s
    session.finished = session.index >= len(session.signs)


def flow_session(words, word_ends, chart, level, length_s):
    """Music: the song's clock, fuses of a few beats, and no time bonus."""
    beat_s = 60.0 / chart.bpm
    return RushSession(words, word_ends, float(length_s), config.FLOW_FUSE_BEATS[level] * beat_s,
                       sign_started_s=chart.first_note_s - beat_s, bpm=chart.bpm, first_beat_s=chart.first_note_s)


def signs_for(length_s):
    """Enough signs that even the fastest run never reaches the end."""
    return int(length_s / config.RUSH_FASTEST_SIGN_S)
