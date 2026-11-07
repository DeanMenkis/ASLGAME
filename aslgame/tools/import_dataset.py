"""Builds sign templates from the ASL-Now fingerspelling landmark dataset."""

import argparse
import json
from pathlib import Path

import numpy as np

from aslgame import config
from aslgame.hand import INDEX_TIP, WRIST
from aslgame.matching.normalize import MIRROR_X, normalize
from aslgame.signs import write_sign

FLIP_ITERATIONS = 5


def load_letter(letter_dir):
    """Return (N, 21, 3) landmarks with x and z rescaled so units match y."""
    samples = []
    for path in sorted(letter_dir.glob("*.json")):
        points = json.loads(path.read_text())
        if len(points) == 21:
            samples.append([[point["x"], point["y"], point["z"]] for point in points])
    scale = np.array([config.DATASET_ASPECT, 1.0, config.DATASET_ASPECT], dtype=np.float32)
    return np.asarray(samples, dtype=np.float32).reshape(-1, 21, 3) * scale


def palm_turn(samples):
    """Signed 2D turn from index base to pinky base. Positive is a right hand palm-out in a mirrored view."""
    index = samples[:, 5, :2] - samples[:, WRIST, :2]
    pinky = samples[:, 17, :2] - samples[:, WRIST, :2]
    return index[:, 0] * pinky[:, 1] - index[:, 1] * pinky[:, 0]


def align_chirality(normalized, side):
    """Mirror samples so every hand in a letter has the same side.

    Seeded by a side cue, then each sample takes whichever side is closer to the median shape.
    """
    mirrored = normalized * MIRROR_X
    use_mirror = side < 0
    for _ in range(FLIP_ITERATIONS):
        median = np.median(np.where(use_mirror[:, None, None], mirrored, normalized), axis=0)
        plain_distance = np.linalg.norm(normalized - median, axis=2).mean(axis=1)
        mirror_distance = np.linalg.norm(mirrored - median, axis=2).mean(axis=1)
        use_mirror = mirror_distance < plain_distance
    return np.where(use_mirror[:, None, None], mirrored, normalized)


def drop_outliers(samples):
    """Remove samples far from the median shape, such as mislabeled or badly tracked hands."""
    distance = np.linalg.norm(samples - np.median(samples, axis=0), axis=2).mean(axis=1)
    return samples[distance <= np.median(distance) * config.DATASET_OUTLIER_FACTOR]


def pointing_side(samples):
    """Positive when the index finger points left in the image, as sideways letters do for a right hand in a mirrored view."""
    return samples[:, WRIST, 0] - samples[:, INDEX_TIP, 0]


def build_letter(letter_dir):
    raw = load_letter(letter_dir)
    normalized = np.stack([normalize(points, False) for points in raw])
    # Sideways hands show little of the palm, so their pointing direction is the reliable side cue.
    side = pointing_side(raw) if letter_dir.name in config.SIDEWAYS_LETTERS else palm_turn(raw)
    aligned = drop_outliers(align_chirality(normalized, side))
    return aligned[: config.DATASET_MAX_SAMPLES]


def main():
    parser = argparse.ArgumentParser(description="Build sign templates from the ASL-Now dataset.")
    parser.add_argument("dataset_dir", type=Path, help="local clone of sid220/asl-now-fingerspelling")
    dataset_dir = parser.parse_args().dataset_dir
    for letter_dir in sorted(path for path in dataset_dir.iterdir() if path.is_dir() and len(path.name) == 1):
        if letter_dir.name in config.MOTION_LETTERS:
            continue
        samples = build_letter(letter_dir)
        write_sign(config.SIGNS_DIR, letter_dir.name, samples)
        print(f"{letter_dir.name}: {len(samples)} samples")


if __name__ == "__main__":
    main()
