"""Charts: a song's tempo and first beat, stored as JSON in data/charts. The words come from the song's deck."""

import json
from dataclasses import dataclass



@dataclass(frozen=True)
class Chart:
    name: str
    title: str
    media: str  # file name inside the media folder
    bpm: float
    first_note_s: float
    deck: str  # name of the word deck signed to this song


def load_charts(charts_dir):
    charts = []
    for path in sorted(charts_dir.glob("*.json")):
        data = json.loads(path.read_text())
        charts.append(Chart(path.stem, data["title"], data["media"], data["bpm"], data["first_note_s"], data["deck"]))
    return sorted(charts, key=lambda chart: chart.bpm)
