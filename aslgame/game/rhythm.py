"""Rhythm mode: notes on a beat, timing judgements, and adaptive speed.

A sign recognized before its beat is locked in and lands on the beat, so a ready hand is never
punished and a fast signer can spell ahead of the ring.
"""

import math
from dataclasses import dataclass, field
from enum import Enum, auto

from aslgame import config
from aslgame.game import match_detector, scoring
from aslgame.game.match_detector import MatchDetector
from aslgame.game.motion import MOTION_SIGNS
from aslgame.game.scoring import Event, EventKind, Judgement, Tally


class NoteState(Enum):
    WAITING = auto()
    APPROACHING = auto()
    HITTABLE = auto()
    HIT = auto()
    MISSED = auto()
    DONE = auto()


OPEN_STATES = (NoteState.WAITING, NoteState.APPROACHING, NoteState.HITTABLE)


@dataclass
class Note:
    sign: str
    due_s: float
    approach_s: float
    window_s: float = config.HIT_WINDOW_S
    index: int = 0
    state: NoteState = NoteState.WAITING
    judgement: Judgement | None = None
    locked_s: float | None = None  # when the sign was recognized
    resolved_s: float = 0.0

    def approach_fraction(self, game_s):
        """1.0 when the note appears, 0.0 when it is due."""
        return min(1.0, max(0.0, (self.due_s - game_s) / self.approach_s))


def judge(late_s, window_s=config.HIT_WINDOW_S):
    """late_s is how long after the beat the sign landed. Early signs wait for the beat, so they count as on time."""
    late = max(0.0, late_s) / window_s
    if late <= config.PERFECT_FRACTION:
        return Judgement.PERFECT
    if late <= config.GOOD_FRACTION:
        return Judgement.GOOD
    return Judgement.OK


def update_note(note, game_s):
    """The note state machine. All transitions happen here."""
    if note.state == NoteState.WAITING and game_s >= note.due_s - note.approach_s:
        note.state = NoteState.APPROACHING
    if note.state == NoteState.APPROACHING and game_s >= note.due_s:
        note.state = NoteState.HITTABLE
    if note.state == NoteState.HITTABLE:
        if note.locked_s is not None:
            note.state = NoteState.HIT
            note.judgement = judge(note.locked_s - note.due_s, note.window_s)
            note.resolved_s = game_s
        elif game_s > note.due_s + note.window_s:
            note.state = NoteState.MISSED
            note.judgement = Judgement.MISS
            note.resolved_s = game_s
    elif note.state in (NoteState.HIT, NoteState.MISSED) and game_s >= note.resolved_s + config.FEEDBACK_S:
        note.state = NoteState.DONE


@dataclass
class RhythmSession:
    signs: list
    word_ends: frozenset = frozenset()  # index of the last sign of each word
    bpm: float = config.RHYTHM_BPM
    beats_per_note: int = config.LEVEL_BEATS_PER_NOTE[0]
    # Music mode fixes the tempo to the song, so speed only adapts in rhythm mode.
    adaptive: bool = True
    speed: float = 1.0
    tally: Tally = field(default_factory=Tally)
    notes: list = field(default_factory=list)  # spawned and not yet done
    next_index: int = 0
    next_due_s: float = config.RHYTHM_LEAD_IN_S
    # No new word starts after this time. None means the run ends when the signs run out.
    last_due_s: float | None = None
    beat_marks: list = field(default_factory=list)  # (due_s, beat_s) of recent and coming notes, for the beat pulse
    recent: list = field(default_factory=list)  # accuracy of recent notes, for speed changes
    detector: MatchDetector = field(default_factory=lambda: MatchDetector(hold_s=config.RHYTHM_HOLD_S))

    def beat_s(self):
        return 60.0 / (self.bpm * self.speed)

    def target(self):
        """The earliest note still waiting to be signed."""
        for note in self.notes:
            if note.state in OPEN_STATES and note.locked_s is None:
                return note
        return None

    def can_spawn(self):
        if self.next_index >= len(self.signs):
            return False
        mid_word = bool(self.word_ends) and self.next_index > 0 and self.next_index - 1 not in self.word_ends
        return self.last_due_s is None or self.next_due_s <= self.last_due_s or mid_word

    def is_finished(self):
        return not self.can_spawn() and not self.notes

    def beat_phase(self, game_s):
        """0.0 on a beat, rising to 1.0 just before the next one."""
        for due_s, beat_s in self.beat_marks:
            if game_s < due_s:
                return ((game_s - due_s) / beat_s) % 1.0
        if self.beat_marks:
            due_s, beat_s = self.beat_marks[-1]
            return ((game_s - due_s) / beat_s) % 1.0
        return (game_s / self.beat_s()) % 1.0


def signs_for(length_s, bpm, beats_per_note):
    """How many signs a run of this length can use, with a word to spare."""
    return int(length_s * bpm / (60.0 * beats_per_note)) + config.LEARN_RUN_SIGNS


def update(session, game_s, target_score):
    """Advance the session. target_score is the current target's score, or None when no hand is seen."""
    spawn_notes(session, game_s)
    target = session.target()
    if target is not None and match_detector.update(session.detector, game_s, target_score):
        target.locked_s = game_s
        session.detector = MatchDetector(hold_s=config.RHYTHM_HOLD_S)
        if game_s < target.due_s:
            session.tally.events.append(Event(EventKind.LOCK))
    for note in session.notes:
        was_open = note.state in OPEN_STATES
        update_note(note, game_s)
        if was_open and note.judgement is not None:
            resolve(session, note)
    session.notes = [note for note in session.notes if note.state != NoteState.DONE]


def motion_slots(interval_s):
    """Note slots a drawn letter takes, so there is time to trace it."""
    return max(config.MOTION_MIN_SLOTS, math.ceil(config.MOTION_MIN_SLOT_S / interval_s))


def spawn_notes(session, game_s):
    while len(session.beat_marks) > 1 and session.beat_marks[1][0] <= game_s:
        session.beat_marks.pop(0)
    beat_s = session.beat_s()
    interval_s = session.beats_per_note * beat_s
    approach_s = config.APPROACH_BEATS * beat_s
    # Spawned a beat before the approach starts, so the next sign is always shown.
    spawn_ahead_s = approach_s + beat_s
    window_s = min(config.HIT_WINDOW_S, interval_s * config.HIT_WINDOW_INTERVAL_FRACTION)
    while session.can_spawn() and session.next_due_s - spawn_ahead_s <= game_s:
        sign = session.signs[session.next_index]
        slots = motion_slots(interval_s) if sign in MOTION_SIGNS else 1
        due_s = session.next_due_s + (slots - 1) * interval_s
        session.notes.append(Note(sign, due_s, approach_s, window_s, session.next_index))
        session.beat_marks.append((due_s, beat_s))
        session.next_index += 1
        session.next_due_s = due_s + interval_s


def resolve(session, note):
    if note.judgement == Judgement.MISS:
        # The missed note was the target, so its half-finished hold must not carry over.
        session.detector = MatchDetector(hold_s=config.RHYTHM_HOLD_S)
    scoring.record(session.tally, note.sign, note.judgement, note.index in session.word_ends, session.speed)
    if session.adaptive:
        adapt_speed(session, scoring.ACCURACY[note.judgement])


def adapt_speed(session, accuracy):
    """Speed up after a run of good notes, slow down after a run of poor ones."""
    session.recent.append(accuracy)
    if len(session.recent) < config.SPEED_WINDOW_NOTES:
        return
    mean = sum(session.recent) / len(session.recent)
    if mean >= config.SPEED_UP_ACCURACY:
        session.speed = min(config.SPEED_MAX, session.speed * config.SPEED_STEP)
    elif mean <= config.SPEED_DOWN_ACCURACY:
        session.speed = max(config.SPEED_MIN, session.speed / config.SPEED_STEP)
    else:
        session.recent.pop(0)
        return
    session.recent.clear()
