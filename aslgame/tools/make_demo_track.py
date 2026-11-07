"""Synthesizes an original demo track into media/ and writes its chart to data/charts."""

import json
import wave

import numpy as np

from aslgame import config

NAME = "demo_90"
TITLE = "Demo 90"
TEXT = "HI ASL CAB GOOD DAY"
BPM = 90
BEATS_PER_NOTE = 4
INTRO_BEATS = 8
OUTRO_BEATS = 8
# One chord root per bar, in Hz: C, A, F, G.
BAR_ROOTS_HZ = (130.81, 110.0, 87.31, 98.0)
VOLUME = 0.3


def tone(duration_s, frequency_hz, decay_per_s):
    t = np.arange(int(duration_s * config.AUDIO_RATE_HZ)) / config.AUDIO_RATE_HZ
    return np.sin(2 * np.pi * frequency_hz * t) * np.exp(-decay_per_s * t)


def kick(duration_s):
    t = np.arange(int(duration_s * config.AUDIO_RATE_HZ)) / config.AUDIO_RATE_HZ
    # A falling pitch gives the thump.
    phase = 2 * np.pi * (50 * t + 60 * (1 - np.exp(-30 * t)) / 30)
    return np.sin(phase) * np.exp(-12 * t)


def hat(duration_s, rng):
    count = int(duration_s * config.AUDIO_RATE_HZ)
    return rng.uniform(-1, 1, count) * np.exp(-60 * np.arange(count) / config.AUDIO_RATE_HZ)


def add(track, start_s, sound, gain):
    start = int(start_s * config.AUDIO_RATE_HZ)
    end = min(len(track), start + len(sound))
    track[start:end] += sound[: end - start] * gain


def synthesize(note_count):
    beat_s = 60.0 / BPM
    total_beats = INTRO_BEATS + note_count * BEATS_PER_NOTE + OUTRO_BEATS
    track = np.zeros(int(total_beats * beat_s * config.AUDIO_RATE_HZ) + config.AUDIO_RATE_HZ)
    rng = np.random.default_rng(0)
    for beat in range(total_beats):
        start_s = beat * beat_s
        root_hz = BAR_ROOTS_HZ[(beat // 4) % len(BAR_ROOTS_HZ)]
        add(track, start_s, kick(beat_s), 0.9)
        add(track, start_s + beat_s / 2, hat(beat_s / 4, rng), 0.15)
        add(track, start_s, tone(beat_s, root_hz, 3), 0.5)
        note_beat = beat - INTRO_BEATS
        if 0 <= note_beat < note_count * BEATS_PER_NOTE and note_beat % BEATS_PER_NOTE == 0:
            # A bright chord on every note so the music marks when to sign.
            for ratio in (2, 2.5, 3):
                add(track, start_s, tone(beat_s, root_hz * ratio, 4), 0.25)
    return track / np.max(np.abs(track)) * VOLUME


def write_wav(path, track):
    samples = (track * 32767).astype(np.int16)
    stereo = np.repeat(samples[:, None], config.AUDIO_CHANNELS, axis=1)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as file:
        file.setnchannels(config.AUDIO_CHANNELS)
        file.setsampwidth(2)
        file.setframerate(config.AUDIO_RATE_HZ)
        file.writeframes(stereo.tobytes())


def main():
    note_count = len(TEXT.replace(" ", ""))
    write_wav(config.MEDIA_DIR / f"{NAME}.wav", synthesize(note_count))
    chart = {
        "title": TITLE,
        "media": f"{NAME}.wav",
        "bpm": BPM,
        "first_note_s": INTRO_BEATS * 60.0 / BPM,
        "beats_per_note": BEATS_PER_NOTE,
        "text": TEXT,
    }
    config.CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    (config.CHARTS_DIR / f"{NAME}.json").write_text(json.dumps(chart, indent=2) + "\n")
    print(f"Wrote {config.MEDIA_DIR / NAME}.wav and {config.CHARTS_DIR / NAME}.json")


if __name__ == "__main__":
    main()
