"""Writes a chart for a song in media/: finds its tempo and first beat, then fills it with signs."""

import argparse
import json
import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import numpy as np  # noqa: E402
import pygame  # noqa: E402

from aslgame import config  # noqa: E402

HOP_SAMPLES = 441
MIN_BPM, MAX_BPM, BPM_STEP = 100.0, 180.0, 0.25
REFINE_RANGE_BPM, REFINE_STEP_BPM = 1.0, 0.05
# Notes start once the beat is this strong compared to the loudest part of the song.
LOUD_FRACTION = 0.5
END_MARGIN_BEATS = 4


def load_mono(path):
    pygame.mixer.init(config.AUDIO_RATE_HZ, config.AUDIO_SAMPLE_BITS, config.AUDIO_CHANNELS)
    samples = pygame.sndarray.array(pygame.mixer.Sound(str(path))).astype(np.float32)
    return samples.mean(axis=1) if samples.ndim == 2 else samples


def onset_envelope(mono):
    """Rises in short-time loudness, which mark drum hits."""
    frames = len(mono) // HOP_SAMPLES
    energy = np.sqrt((mono[: frames * HOP_SAMPLES].reshape(frames, HOP_SAMPLES) ** 2).mean(axis=1))
    onset = np.maximum(0.0, np.diff(energy, prepend=energy[0]))
    return onset - onset.mean(), energy


def find_bpm(onset, frames_per_s):
    """The tempo whose beat, two-beat, and bar spacing best line up with the onsets."""
    best_bpm, best_score = MIN_BPM, -np.inf
    for bpm in np.arange(MIN_BPM, MAX_BPM + BPM_STEP, BPM_STEP):
        score = 0.0
        for multiple in (1, 2, 4):
            lag = int(round(60.0 / bpm * frames_per_s * multiple))
            score += float((onset[:-lag] * onset[lag:]).sum())
        if score > best_score:
            best_bpm, best_score = bpm, score
    return best_bpm


def grid_strength(onset, frames_per_s, bpm, phase_s):
    """Mean onset on the beat grid across the whole song. A slightly wrong tempo drifts off the beat and scores low."""
    frames = ((np.arange(phase_s, len(onset) / frames_per_s, 60.0 / bpm)) * frames_per_s).round().astype(int)
    frames = frames[frames < len(onset)]
    return float(onset[frames].mean())


def refine_bpm(onset, frames_per_s, coarse_bpm):
    """Search near the rough tempo for the one that stays on the beat from start to end."""
    best = (-np.inf, coarse_bpm, 0.0)
    for bpm in np.arange(coarse_bpm - REFINE_RANGE_BPM, coarse_bpm + REFINE_RANGE_BPM + REFINE_STEP_BPM, REFINE_STEP_BPM):
        phase_s = find_phase_s(onset, frames_per_s, bpm)
        best = max(best, (grid_strength(onset, frames_per_s, bpm, phase_s), bpm, phase_s))
    return best[1], best[2]


def find_phase_s(onset, frames_per_s, bpm):
    """Offset of the beat grid: the shift that puts the most onset energy on beats."""
    beat_frames = 60.0 / bpm * frames_per_s
    offsets = np.arange(0.0, beat_frames, 0.5)
    positions = np.arange(len(onset))
    scores = [onset[(np.abs(((positions - offset) % beat_frames)) < 1.0)].sum() for offset in offsets]
    return offsets[int(np.argmax(scores))] / frames_per_s


def main():
    parser = argparse.ArgumentParser(description="Write a chart for a song in media/.")
    parser.add_argument("media", help="file name inside media/")
    parser.add_argument("title")
    parser.add_argument("--text", default="HI ASL LOVE GOOD DAY CAB THANK YOU", help="words to sign, repeated to fill the song")
    parser.add_argument("--beats-per-note", type=int, default=4)
    args = parser.parse_args()

    mono = load_mono(config.MEDIA_DIR / args.media)
    frames_per_s = config.AUDIO_RATE_HZ / HOP_SAMPLES
    onset, energy = onset_envelope(mono)
    bpm, phase_s = refine_bpm(onset, frames_per_s, find_bpm(onset, frames_per_s))
    beat_s = 60.0 / bpm
    duration_s = len(mono) / config.AUDIO_RATE_HZ
    loud_frame = int(np.argmax(energy > energy.max() * LOUD_FRACTION))
    first_beat = int(np.ceil((loud_frame / frames_per_s - phase_s) / beat_s))
    # Start on a bar line, and leave room for the approach ring.
    first_beat = max(first_beat + (-first_beat) % 4, config.APPROACH_BEATS + 1)
    first_note_s = phase_s + first_beat * beat_s
    note_count = int((duration_s - first_note_s) / beat_s - END_MARGIN_BEATS) // args.beats_per_note

    words = args.text.upper().split()
    text, letters = [], 0
    while letters < note_count:
        word = words[len(text) % len(words)][: note_count - letters]
        text.append(word)
        letters += len(word)

    chart = {
        "title": args.title,
        "media": args.media,
        "bpm": round(float(bpm), 2),
        "first_note_s": round(float(first_note_s), 3),
        "beats_per_note": args.beats_per_note,
        "text": " ".join(text),
    }
    name = os.path.splitext(args.media)[0]
    (config.CHARTS_DIR / f"{name}.json").write_text(json.dumps(chart, indent=2) + "\n")
    print(f"{args.title}: {bpm:.2f} BPM, first note {first_note_s:.2f} s, {letters} signs over {duration_s:.0f} s")


if __name__ == "__main__":
    main()
