import json
from pathlib import Path

HISTORY_FILE = Path("history.json")

def load_history():
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return []

def save_history(history):
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")

def reset_history():
    if HISTORY_FILE.exists():
        HISTORY_FILE.unlink()
