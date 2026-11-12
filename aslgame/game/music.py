"""Music mode: sign each letter before its fuse runs out; the next one appears the moment you land it.

The song is the clock. Fuses are counted in beats, faster signs judge better, and a sign that lands on a beat scores more.
"""

from dataclasses import dataclass, field

from aslgame import config
from aslgame.game import match_detector, scoring
from aslgame.game.match_detector import MatchDetector
from aslgame.game.motion import MOTION_SIGNS
from aslgame.game.scoring import Judgement, Tally
from aslgame.game.sign_queue import word_ends


@dataclass
class MusicSession:
    signs: list
    word_ends: frozenset
    length_s: float
    bpm: float
    first_beat_s: float
    fuse_beats: float  # how many beats one sign may take before it is missed
    tally: Tally = field(default_factory=Tally)
    index: int = 0
    sign_started_s: float = 0.0
    detector: MatchDetector = field(default_factory=lambda: MatchDetector(hold_s=config.TIMED_HOLD_S))
    finished: bool = False
    on_beats: int = 0

    def __post_init__(self):
        # The first fuse is lit a beat before the first beat, so the first sign can land on it.
        self.sign_started_s = self.first_beat_s - self.beat_s()

    def beat_s(self):
        return 60.0 / self.bpm

    def fuse_s(self):
        """How long the current sign may take. Drawn letters get longer."""
        factor = config.MOTION_FUSE_FACTOR if self.signs[self.index] in MOTION_SIGNS else 1.0
        return self.fuse_beats * self.beat_s() * factor

    def beat_phase(self, game_s):
        """0.0 on a beat, rising to 1.0 just before the next."""
        return ((game_s - self.first_beat_s) / self.beat_s()) % 1.0

    def beat_offset_s(self, game_s):
        """Distance to the nearest beat."""
        phase = self.beat_phase(game_s)
        return min(phase, 1.0 - phase) * self.beat_s()

    def target(self):
        return None if self.finished else self.signs[self.index]

    def is_finished(self):
        return self.finished

    def time_left_s(self, game_s):
        return max(0.0, self.length_s - game_s)

    def fuse_fraction(self, game_s):
        """1.0 when the sign appears, 0.0 when its fuse has run out."""
        used = (game_s - self.sign_started_s) / self.fuse_s()
        return min(1.0, max(0.0, 1.0 - used))


def judge(took_s, fuse_s):
    """By speed, as a share of the fuse, so the limits follow the song's tempo."""
    if took_s <= fuse_s * config.PERFECT_FRACTION:
        return Judgement.PERFECT
    if took_s <= fuse_s * config.GOOD_FRACTION:
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
    if match_detector.update(session.detector, game_s, target_score):
        advance(session, game_s, judge(game_s - session.sign_started_s, session.fuse_s()))
    elif session.fuse_fraction(game_s) <= 0.0:
        advance(session, game_s, Judgement.MISS)


def advance(session, game_s, judgement):
    on_beat = judgement != Judgement.MISS and session.beat_offset_s(game_s) <= config.ON_BEAT_WINDOW_S
    session.on_beats += on_beat
    scoring.record(session.tally, session.signs[session.index], judgement, session.index in session.word_ends,
                   bonus=config.ON_BEAT_BONUS if on_beat else 1.0)
    session.detector = MatchDetector(hold_s=config.TIMED_HOLD_S)
    session.index += 1
    session.sign_started_s = game_s
    session.finished = session.index >= len(session.signs)


def make_session(words, chart, level, length_s):
    signs = [letter for word in words for letter in word]
    return MusicSession(signs, word_ends(words), float(length_s), chart.bpm, chart.first_note_s, config.FUSE_BEATS[level])


def signs_for(length_s):
    """Enough signs that even the fastest run never reaches the end."""
    return int(length_s / config.FASTEST_SIGN_S)
