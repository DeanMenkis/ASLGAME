"""Charts: the signs of a song and when they fall, stored as JSON in data/charts."""

import json
from dataclasses import dataclass

from aslgame import config
from aslgame.game.rhythm import RhythmSession
from aslgame.game.sign_queue import make_queue


@dataclass(frozen=True)
class Chart:
    name: str
    title: str
    media: str  # file name inside the media folder, which is never committed
    bpm: float
    first_note_s: float
    beats_per_note: int
    text: str


def load_charts(charts_dir):
    charts = []
    for path in sorted(charts_dir.glob("*.json")):
        data = json.loads(path.read_text())
        charts.append(Chart(path.stem, data["title"], data["media"], data["bpm"], data["first_note_s"],
                            data["beats_per_note"], data["text"]))
    return charts


def make_session(chart):
    """A rhythm session locked to the song: fixed tempo, notes from the chart."""
    queue = make_queue(chart.text)
    signs = [queue.text[index] for index in queue.positions]
    return RhythmSession(
        signs[:note_count(chart)],
        bpm=chart.bpm,
        beats_per_note=chart.beats_per_note,
        adaptive=False,
        next_due_s=chart.first_note_s,
    )


def note_count(chart):
    """How many notes fit in the music time limit, counting the last note's hit window and feedback."""
    interval_s = chart.beats_per_note * 60.0 / chart.bpm
    last_due_s = config.MUSIC_MAX_S - config.HIT_WINDOW_S - config.FEEDBACK_S
    return max(1, int((last_due_s - chart.first_note_s) // interval_s) + 1)
