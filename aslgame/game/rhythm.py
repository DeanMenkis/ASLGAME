"""Rhythm mode: notes on a beat, timing judgements, score, combo, and adaptive speed."""

from dataclasses import dataclass, field
from enum import Enum, auto

from aslgame import config
from aslgame.game import match_detector
from aslgame.game.match_detector import DetectorState, MatchDetector


class NoteState(Enum):
    WAITING = auto()
    APPROACHING = auto()
    HITTABLE = auto()
    HIT = auto()
    MISSED = auto()
    DONE = auto()


class Judgement(Enum):
    PERFECT = auto()
    GOOD = auto()
    OK = auto()
    MISS = auto()


POINTS = {Judgement.PERFECT: 300, Judgement.GOOD: 100, Judgement.OK: 50, Judgement.MISS: 0}
ACCURACY = {Judgement.PERFECT: 1.0, Judgement.GOOD: 0.7, Judgement.OK: 0.4, Judgement.MISS: 0.0}


@dataclass
class Note:
    sign: str
    due_s: float
    approach_s: float
    state: NoteState = NoteState.WAITING
    judgement: Judgement | None = None
    resolved_s: float = 0.0

    def approach_fraction(self, game_s):
        """1.0 when the note appears, 0.0 when it is due."""
        return min(1.0, max(0.0, (self.due_s - game_s) / self.approach_s))


def judge(offset_s):
    offset_s = abs(offset_s)
    if offset_s <= config.PERFECT_WINDOW_S:
        return Judgement.PERFECT
    if offset_s <= config.GOOD_WINDOW_S:
        return Judgement.GOOD
    return Judgement.OK


def update_note(note, game_s, matched, latency_offset_s=0.0):
    """The note state machine. All transitions happen here."""
    if note.state == NoteState.WAITING and game_s >= note.due_s - note.approach_s:
        note.state = NoteState.APPROACHING
    if note.state == NoteState.APPROACHING and game_s >= note.due_s - config.HIT_WINDOW_S:
        note.state = NoteState.HITTABLE
    if note.state == NoteState.HITTABLE:
        if matched:
            note.state = NoteState.HIT
            note.judgement = judge(game_s - latency_offset_s - note.due_s)
            note.resolved_s = game_s
        elif game_s > note.due_s + config.HIT_WINDOW_S:
            note.state = NoteState.MISSED
            note.judgement = Judgement.MISS
            note.resolved_s = game_s
    elif note.state in (NoteState.HIT, NoteState.MISSED) and game_s >= note.resolved_s + config.FEEDBACK_S:
        note.state = NoteState.DONE


@dataclass
class RhythmSession:
    signs: list
    bpm: float = config.RHYTHM_BPM
    beats_per_note: int = config.BEATS_PER_NOTE
    # Music mode fixes the tempo to the song, so speed only adapts in rhythm mode.
    adaptive: bool = True
    latency_offset_s: float = 0.0
    speed: float = 1.0
    score: int = 0
    combo: int = 0
    max_combo: int = 0
    notes: list = field(default_factory=list)  # spawned and not yet done
    next_index: int = 0
    next_due_s: float = config.RHYTHM_LEAD_IN_S
    due_times: list = field(default_factory=list)
    recent: list = field(default_factory=list)  # accuracy of recent notes, for speed changes
    results: list = field(default_factory=list)  # (sign, judgement) of every resolved note
    detector: MatchDetector = field(default_factory=lambda: MatchDetector(hold_s=config.RHYTHM_HOLD_S))

    def beat_s(self):
        return 60.0 / (self.bpm * self.speed)

    def target(self):
        """The earliest note still waiting to be signed."""
        for note in self.notes:
            if note.state in (NoteState.WAITING, NoteState.APPROACHING, NoteState.HITTABLE):
                return note
        return None

    def is_finished(self):
        return self.next_index >= len(self.signs) and not self.notes

    def beat_phase(self, game_s):
        """0.0 on a beat, rising to 1.0 just before the next one."""
        previous_s = 0.0
        for due_s in self.due_times + [self.next_due_s]:
            if game_s < due_s:
                beat_s = (due_s - previous_s) / self.beats_per_note if previous_s else self.beat_s()
                return ((game_s - due_s) / beat_s) % 1.0
            previous_s = due_s
        return ((game_s - previous_s) / self.beat_s()) % 1.0


def update(session, game_s, target_score):
    """Advance the session. target_score is the current target's score, or None when no hand is seen."""
    spawn_notes(session, game_s)
    target = session.target()
    if target is not None:
        match_detector.update(session.detector, game_s, target_score)
    matched = session.detector.state == DetectorState.MATCHED
    for note in session.notes:
        was_open = note.state in (NoteState.WAITING, NoteState.APPROACHING, NoteState.HITTABLE)
        update_note(note, game_s, matched and note is target, session.latency_offset_s)
        if was_open and note.judgement is not None:
            resolve(session, note)
    session.notes = [note for note in session.notes if note.state != NoteState.DONE]


def spawn_notes(session, game_s):
    beat_s = session.beat_s()
    approach_s = config.APPROACH_BEATS * beat_s
    # Spawned a beat before the approach starts, so the next sign is always shown.
    spawn_ahead_s = approach_s + beat_s
    while session.next_index < len(session.signs) and session.next_due_s - spawn_ahead_s <= game_s:
        session.notes.append(Note(session.signs[session.next_index], session.next_due_s, approach_s))
        session.due_times.append(session.next_due_s)
        session.next_index += 1
        session.next_due_s += session.beats_per_note * beat_s


def resolve(session, note):
    session.results.append((note.sign, note.judgement))
    session.detector = MatchDetector(hold_s=config.RHYTHM_HOLD_S)
    if note.judgement == Judgement.MISS:
        session.combo = 0
    else:
        session.combo += 1
        session.max_combo = max(session.max_combo, session.combo)
    multiplier = 1.0 + min(session.combo, config.COMBO_CAP) / config.COMBO_STEP
    session.score += int(POINTS[note.judgement] * multiplier)
    if session.adaptive:
        adapt_speed(session, ACCURACY[note.judgement])


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


@dataclass(frozen=True)
class Results:
    score: int
    max_combo: int
    accuracy: float
    counts: dict
    weakest: list  # (sign, accuracy), weakest first


def summarize(session):
    counts = {judgement: 0 for judgement in Judgement}
    per_sign = {}
    for sign, judgement in session.results:
        counts[judgement] += 1
        per_sign.setdefault(sign, []).append(ACCURACY[judgement])
    accuracy = sum(ACCURACY[j] for _, j in session.results) / len(session.results) if session.results else 0.0
    sign_accuracy = sorted(((sign, sum(v) / len(v)) for sign, v in per_sign.items()), key=lambda item: item[1])
    weakest = [item for item in sign_accuracy if item[1] < 1.0][: config.RESULTS_WEAKEST_COUNT]
    return Results(session.score, session.max_combo, accuracy, counts, weakest)
