"""Turns noisy per-frame match scores into one clean matched event."""

from dataclasses import dataclass
from enum import Enum, auto

from aslgame import config


class DetectorState(Enum):
    NO_HAND = auto()
    SEARCHING = auto()
    HOLDING = auto()
    MATCHED = auto()


@dataclass
class MatchDetector:
    hold_s: float = config.MATCH_HOLD_S
    state: DetectorState = DetectorState.NO_HAND
    hold_started_s: float = 0.0
    hold_fraction: float = 0.0


def update(detector, now_s, score):
    """The detector state machine. score is None when no hand is seen. Return True on the matched frame."""
    if score is None:
        detector.state = DetectorState.NO_HAND
        detector.hold_fraction = 0.0
        return False
    if detector.state in (DetectorState.NO_HAND, DetectorState.SEARCHING):
        if score >= config.MATCH_THRESHOLD:
            detector.state = DetectorState.HOLDING
            detector.hold_started_s = now_s
        else:
            detector.state = DetectorState.SEARCHING
        return False
    if detector.state == DetectorState.HOLDING:
        # A lower release threshold stops jitter near the threshold from restarting the hold.
        if score < config.MATCH_RELEASE_THRESHOLD:
            detector.state = DetectorState.SEARCHING
            detector.hold_fraction = 0.0
            return False
        detector.hold_fraction = min(1.0, (now_s - detector.hold_started_s) / detector.hold_s)
        if detector.hold_fraction >= 1.0:
            detector.state = DetectorState.MATCHED
            return True
    return False
