"""Charts: a song's tempo and first beat, stored as JSON in data/charts. The words come from the song's deck."""

import json
from dataclasses import dataclass

from aslgame import config
from aslgame.game.rhythm import RhythmSession, signs_for
from aslgame.game.sign_queue import word_ends


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


def play_length_s(length_s, track_s):
    """The chosen run length, or the whole song when it is shorter."""
    return min(length_s, track_s - config.MUSIC_END_MARGIN_S)


def signs_needed(chart, level, length_s):
    return signs_for(length_s, chart.bpm, config.LEVEL_BEATS_PER_NOTE[level])


def make_session(chart, words, level, length_s):
    """A rhythm session locked to the song: fixed tempo, and no new word once length_s has passed."""
    return RhythmSession(
        [letter for word in words for letter in word],
        word_ends(words),
        bpm=chart.bpm,
        beats_per_note=config.LEVEL_BEATS_PER_NOTE[level],
        adaptive=False,
        next_due_s=chart.first_note_s,
        last_due_s=length_s - config.HIT_WINDOW_S - config.FEEDBACK_S,
    )
