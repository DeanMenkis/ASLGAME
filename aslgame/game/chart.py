"""Charts: the signs of a song and when they fall, stored as JSON in data/charts."""

import json
from dataclasses import dataclass

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
    return RhythmSession(
        [queue.text[index] for index in queue.positions],
        bpm=chart.bpm,
        beats_per_note=chart.beats_per_note,
        adaptive=False,
        next_due_s=chart.first_note_s,
    )
