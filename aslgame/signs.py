"""Sign templates: recorded normalized hands, one JSON file per sign."""

import json
from dataclasses import dataclass

import numpy as np

DECIMALS = 4


@dataclass(frozen=True)
class Sign:
    name: str
    samples: np.ndarray  # (N, 21, 3) normalized hands
    outline: np.ndarray  # (21, 3) mean of samples, drawn as the ghost hand


def make_sign(name, samples):
    samples = np.asarray(samples, dtype=np.float32)
    outline = samples.mean(axis=0)
    # The outline is what the player is shown, so copying it exactly must always match.
    return Sign(name, np.concatenate([samples, outline[None]]), outline)


def load_signs(signs_dir):
    """Load every sign in signs_dir, keyed and ordered by name."""
    signs = {}
    for path in sorted(signs_dir.glob("*.json")):
        data = json.loads(path.read_text())
        signs[data["name"]] = make_sign(data["name"], data["samples"])
    return signs


def save_sign(signs_dir, name, new_samples):
    """Append samples to a sign's file, creating it if needed."""
    path = signs_dir / f"{name}.json"
    samples = json.loads(path.read_text())["samples"] if path.exists() else []
    return write_sign(signs_dir, name, samples + np.round(np.asarray(new_samples), DECIMALS).tolist())


def write_sign(signs_dir, name, samples):
    """Replace a sign's file with these samples."""
    samples = np.round(np.asarray(samples), DECIMALS).tolist()
    signs_dir.mkdir(parents=True, exist_ok=True)
    (signs_dir / f"{name}.json").write_text(json.dumps({"name": name, "samples": samples}))
    return len(samples)
