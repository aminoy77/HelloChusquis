"""Deprecated compatibility memory with safe local persistence."""

import json
import os
import secrets
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

MEMORY_DIR = Path.home() / ".hellochusquis"
SESSIONS_DIR = MEMORY_DIR / "sessions"
MEMORY_FILE = MEMORY_DIR / "memory.json"


def _private_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path, 0o700)


def _atomic_json_write(path: Path, data: dict) -> None:
    """Write JSON atomically with owner-only file permissions."""
    fd, temporary_path = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as temporary_file:
            json.dump(data, temporary_file, indent=2)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, path)
    finally:
        if os.path.exists(temporary_path):
            os.unlink(temporary_path)


def init() -> None:
    _private_dir(MEMORY_DIR)
    _private_dir(SESSIONS_DIR)
    if not MEMORY_FILE.exists():
        _atomic_json_write(MEMORY_FILE, {"summary": "", "updated_at": None})


def load_summary() -> str:
    init()
    try:
        data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, TypeError):
        return ""
    summary = data.get("summary", "")
    return summary if isinstance(summary, str) else ""


def save_summary(summary: str) -> None:
    init()
    _atomic_json_write(
        MEMORY_FILE,
        {"summary": str(summary), "updated_at": datetime.now().isoformat()},
    )


def save_session(messages: list[dict]) -> None:
    """Save a session under a collision-resistant timestamped filename."""
    init()
    if not messages:
        return
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H%M%S_%f")
    session_id = f"{timestamp}_{secrets.token_hex(4)}"
    _atomic_json_write(
        SESSIONS_DIR / f"{session_id}.json",
        {"timestamp": now.isoformat(), "messages": messages},
    )


def cleanup_old_sessions(days: int) -> None:
    init()
    cutoff = datetime.now() - timedelta(days=max(0, int(days)))
    for session_file in SESSIONS_DIR.glob("*.json"):
        try:
            prefix = session_file.stem.split("_", 3)
            if len(prefix) >= 3:
                date_text = "_".join(prefix[:3])
                file_date = datetime.strptime(date_text, "%Y-%m-%d_%H%M%S")
            else:
                file_date = datetime.strptime(session_file.stem, "%Y-%m-%d_%H%M%S")
            if file_date < cutoff:
                session_file.unlink()
        except (OSError, ValueError):
            continue
