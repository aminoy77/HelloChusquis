# DEPRECATED: This module is not used. Consider removing.
# Use core.db_memory instead for database-backed memory.
import json
from datetime import datetime, timedelta
from pathlib import Path


MEMORY_DIR = Path.home() / ".hellochusquis"
SESSIONS_DIR = MEMORY_DIR / "sessions"
MEMORY_FILE = MEMORY_DIR / "memory.json"


def init():
    MEMORY_DIR.mkdir(exist_ok=True)
    SESSIONS_DIR.mkdir(exist_ok=True)
    if not MEMORY_FILE.exists():
        MEMORY_FILE.write_text(json.dumps({
            "summary": "",
            "updated_at": None,
        }, indent=2))


def load_summary() -> str:
    init()
    data = json.loads(MEMORY_FILE.read_text())
    return data.get("summary", "")


def save_summary(summary: str):
    init()
    MEMORY_FILE.write_text(json.dumps({
        "summary": summary,
        "updated_at": datetime.now().isoformat(),
    }, indent=2))


def save_session(messages: list[dict]):
    init()
    if not messages:
        return
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    path = SESSIONS_DIR / f"{timestamp}.json"
    path.write_text(json.dumps({
        "timestamp": timestamp,
        "messages": messages,
    }, indent=2))


def cleanup_old_sessions(days: int):
    init()
    cutoff = datetime.now() - timedelta(days=days)
    for f in SESSIONS_DIR.glob("*.json"):
        try:
            file_date = datetime.strptime(f.stem, "%Y-%m-%d_%H%M%S")
            if file_date < cutoff:
                f.unlink()
        except Exception:
            continue
