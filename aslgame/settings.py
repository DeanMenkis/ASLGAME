"""Player settings saved between runs in a local file. Read at startup and written at exit only."""

import json
from dataclasses import asdict, dataclass

from aslgame import config


@dataclass
class Settings:
    latency_offset_ms: int = config.LATENCY_OFFSET_DEFAULT_MS


def load_settings(path):
    if not path.exists():
        return Settings()
    try:
        return Settings(**json.loads(path.read_text()))
    except (ValueError, TypeError):
        return Settings()


def save_settings(path, settings):
    path.write_text(json.dumps(asdict(settings), indent=2))
