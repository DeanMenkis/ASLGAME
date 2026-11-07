"""Player settings saved between runs in a local file. Read at startup and written at exit only."""

import json
from dataclasses import asdict, dataclass, fields


@dataclass
class Settings:
    finger_colors: bool = False
    sound: bool = True


def load_settings(path):
    if not path.exists():
        return Settings()
    try:
        saved = json.loads(path.read_text())
    except ValueError:
        return Settings()
    # Unknown keys from older versions are ignored.
    known = {field.name for field in fields(Settings)}
    return Settings(**{key: value for key, value in saved.items() if key in known})


def save_settings(path, settings):
    path.write_text(json.dumps(asdict(settings), indent=2))
