"""Player settings saved between runs in a local file. Read at startup and written at exit only."""

import json
from dataclasses import asdict, dataclass, fields


@dataclass
class Settings:
    finger_colors: bool = False
    sound: bool = True
    # Rising dots, flying paper, shake, and slipping plates. Off keeps the print look and holds it still.
    motion: bool = True
    # The camera printed in the game's inks. Off shows the plain camera picture, for anyone who sees their hand better that way.
    print_camera: bool = True


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
