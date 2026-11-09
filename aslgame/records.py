"""Best scores saved between runs in a local file. Read at startup and written at exit only."""

import json


def record_key(mode, item, level, length_s):
    return f"{mode}/{item}/{level}/{length_s}"


def load_records(path):
    if not path.exists():
        return {}
    try:
        saved = json.loads(path.read_text())
    except ValueError:
        return {}
    return saved if isinstance(saved, dict) else {}


def save_records(path, records):
    path.write_text(json.dumps(records, indent=2))


def update_record(records, key, score, grade):
    """Keep the higher score. Returns True when this run set a new best."""
    best = records.get(key)
    if best is not None and best["score"] >= score:
        return False
    records[key] = {"score": score, "grade": grade}
    return True
