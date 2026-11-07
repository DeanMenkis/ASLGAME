"""Synthesizes original demo tracks into media/ and writes their charts to data/charts."""

import json
import wave
from dataclasses import dataclass

import numpy as np

from aslgame import config

RATE = config.AUDIO_RATE_HZ
INTRO_BEATS = 8
OUTRO_BEATS = 8
VOLUME = 0.32
# Chord roots in Hz, one per bar.
WARMUP_ROOTS_HZ = (130.81, 110.0, 87.31, 98.0)  # C A F G
HARDSTYLE_ROOTS_HZ = (110.0, 87.31, 130.81, 98.0)  # Am F C G
MINOR_CHORD = (1.0, 1.189, 1.498)
MAJOR_CHORD = (1.0, 1.26, 1.498)


@dataclass(frozen=True)
class Track:
    name: str
    title: str
    bpm: int
    text: str
    style: str


TRACKS = (
    Track("demo_90", "Warm-up 90", 90, "HI ASL CAB GOOD DAY", "warmup"),
    Track("hardstyle_150", "Hardstyle 150", 150, "HI ASL LOVE GOOD DAY CAB THANK YOU HI LOVE", "hardstyle"),
)


def seconds(count_s):
    return np.arange(int(count_s * RATE)) / RATE


def tone(duration_s, frequency_hz, decay_per_s):
    t = seconds(duration_s)
    return np.sin(2 * np.pi * frequency_hz * t) * np.exp(-decay_per_s * t)


def soft_kick(duration_s):
    t = seconds(duration_s)
    return np.sin(2 * np.pi * (50 * t + 2 * (1 - np.exp(-30 * t)))) * np.exp(-12 * t)


def hard_kick(duration_s):
    """Pitch drops fast from a click to a low tone, then distortion gives the long gritty tail."""
    t = seconds(duration_s)
    frequency_hz = 55 + 260 * np.exp(-28 * t)
    phase = 2 * np.pi * np.cumsum(frequency_hz) / RATE
    body = np.sin(phase) * np.exp(-5.5 * t)
    return np.tanh(body * 5.0) * 0.9


def reverse_bass(duration_s, frequency_hz):
    """Swells up into the next kick, the classic hardstyle bounce."""
    t = seconds(duration_s)
    swell = (t / t[-1]) ** 2
    return np.tanh(np.sin(2 * np.pi * frequency_hz * t) * 3.0) * swell * 0.55


def noise(duration_s, rng, decay_per_s):
    t = seconds(duration_s)
    return rng.uniform(-1, 1, len(t)) * np.exp(-decay_per_s * t)


def supersaw(duration_s, frequency_hz, decay_per_s):
    """Several slightly detuned saws: the wide hardstyle lead."""
    t = seconds(duration_s)
    wave_sum = sum(2 * ((frequency_hz * detune * t) % 1.0) - 1 for detune in (0.99, 0.995, 1.0, 1.005, 1.01))
    return wave_sum / 5 * np.exp(-decay_per_s * t)


def add(track, start_s, sound, gain):
    start = int(start_s * RATE)
    end = min(len(track), start + len(sound))
    if end > start:
        track[start:end] += sound[: end - start] * gain


def is_note_beat(beat, note_count):
    note_beat = beat - INTRO_BEATS
    return 0 <= note_beat < note_count * config.BEATS_PER_NOTE and note_beat % config.BEATS_PER_NOTE == 0


def warmup(bpm, note_count):
    beat_s = 60.0 / bpm
    total_beats = INTRO_BEATS + note_count * config.BEATS_PER_NOTE + OUTRO_BEATS
    track = np.zeros(int((total_beats + 1) * beat_s * RATE))
    rng = np.random.default_rng(0)
    for beat in range(total_beats):
        start_s = beat * beat_s
        root_hz = WARMUP_ROOTS_HZ[(beat // 4) % len(WARMUP_ROOTS_HZ)]
        add(track, start_s, soft_kick(beat_s), 0.9)
        add(track, start_s + beat_s / 2, noise(beat_s / 4, rng, 60), 0.15)
        add(track, start_s, tone(beat_s, root_hz, 3), 0.5)
        if is_note_beat(beat, note_count):
            for ratio in MAJOR_CHORD:
                add(track, start_s, tone(beat_s, root_hz * 2 * ratio, 4), 0.25)
    return track


def hardstyle(bpm, note_count):
    beat_s = 60.0 / bpm
    total_beats = INTRO_BEATS + note_count * config.BEATS_PER_NOTE + OUTRO_BEATS
    track = np.zeros(int((total_beats + 1) * beat_s * RATE))
    rng = np.random.default_rng(1)
    for beat in range(total_beats):
        start_s = beat * beat_s
        root_hz = HARDSTYLE_ROOTS_HZ[(beat // 4) % len(HARDSTYLE_ROOTS_HZ)]
        if beat < INTRO_BEATS:
            # Intro: a riser and a ticking hat build up to the drop.
            add(track, start_s, noise(beat_s, rng, 1.0) * (beat + 1) / INTRO_BEATS, 0.12)
            add(track, start_s, noise(0.03, rng, 120), 0.3)
            for ratio in MINOR_CHORD:
                add(track, start_s, supersaw(beat_s, root_hz * 2 * ratio, 2), 0.12)
            continue
        add(track, start_s, hard_kick(beat_s * 0.55), 1.0)
        add(track, start_s + beat_s * 0.5, reverse_bass(beat_s * 0.5, root_hz / 2), 1.0)
        add(track, start_s + beat_s * 0.5, noise(beat_s / 3, rng, 40), 0.14)
        if beat % 2 == 1:
            add(track, start_s, noise(0.15, rng, 25), 0.35)  # clap on 2 and 4
        if is_note_beat(beat, note_count):
            # A loud chord stab on every sign, so the music marks when to sign.
            for ratio in MINOR_CHORD:
                add(track, start_s, supersaw(beat_s * 2, root_hz * 4 * ratio, 3), 0.2)
    return np.tanh(track * 1.5)


def write_wav(path, track):
    track = track / np.max(np.abs(track)) * VOLUME
    samples = (track * 32767).astype(np.int16)
    stereo = np.repeat(samples[:, None], config.AUDIO_CHANNELS, axis=1)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as file:
        file.setnchannels(config.AUDIO_CHANNELS)
        file.setsampwidth(2)
        file.setframerate(RATE)
        file.writeframes(stereo.tobytes())


def main():
    styles = {"warmup": warmup, "hardstyle": hardstyle}
    config.CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    for track in TRACKS:
        note_count = len(track.text.replace(" ", ""))
        write_wav(config.MEDIA_DIR / f"{track.name}.wav", styles[track.style](track.bpm, note_count))
        chart = {
            "title": track.title,
            "media": f"{track.name}.wav",
            "bpm": track.bpm,
            "first_note_s": INTRO_BEATS * 60.0 / track.bpm,
            "beats_per_note": config.BEATS_PER_NOTE,
            "text": track.text,
        }
        (config.CHARTS_DIR / f"{track.name}.json").write_text(json.dumps(chart, indent=2) + "\n")
        print(f"Wrote {track.title}: {note_count} signs")


if __name__ == "__main__":
    main()
