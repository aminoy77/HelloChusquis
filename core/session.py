"""
Session management, conversation compaction, context-window guarding, and prompt
composition for HelloChusquis.

Dependencies: stdlib only (sqlite3, hashlib, json, time, uuid, re, textwrap, threading).
Optional: tiktoken for accurate token counts (falls back to char/4 estimation).
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import textwrap
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Sequence

# ---------------------------------------------------------------------------
# Optional tiktoken import (lazy: BPE ranks cost ~90ms at import)
# ---------------------------------------------------------------------------
_tiktoken = None
_ENCODER = None
_ENCODER_LOADED = False


def _get_encoder():
    global _tiktoken, _ENCODER, _ENCODER_LOADED
    if not _ENCODER_LOADED:
        _ENCODER_LOADED = True
        try:
            import tiktoken as _mod
            _tiktoken = _mod
            _ENCODER = _mod.get_encoding("cl100k_base")
        except ImportError:
            _ENCODER = None
    return _ENCODER


# ===========================================================================
# Token estimation helpers
# ===========================================================================

def estimate_tokens(text: str) -> int:
    """Return approximate token count for *text*.

    Uses tiktoken when available, otherwise falls back to ``len(text) // 4``.
    """
    encoder = _get_encoder()
    if encoder is not None:
        return len(encoder.encode(text))
    return max(1, len(text) // 4)


def estimate_message_tokens(message: dict[str, Any]) -> int:
    """Estimate tokens for a single chat message dict."""
    content = message.get("content", "")
    if isinstance(content, list):
        # Multimodal: sum text parts
        parts = [p.get("text", "") for p in content if isinstance(p, dict)]
        content = "\n".join(parts)
    role_overhead = 4  # role tag overhead
    return role_overhead + estimate_tokens(content)


def estimate_messages_tokens(messages: Sequence[dict[str, Any]]) -> int:
    """Sum token estimates for a list of messages."""
    return sum(estimate_message_tokens(m) for m in messages)


# ===========================================================================
# Data classes
# ===========================================================================

class SessionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"


@dataclass
class SessionMetadata:
    """Metadata attached to a session row."""
    session_id: str
    agent_id: str
    title: str
    created_at: float
    updated_at: float
    status: SessionStatus
    model: str
    context_window: int
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class CompactionResult:
    """Outcome of a compaction pass."""
    messages: list[dict[str, Any]]
    tokens_before: int
    tokens_after: int
    strategy_used: str
    dropped_count: int
    summary_text: str | None = None


# ===========================================================================
# Constants
# ===========================================================================

DEFAULT_CONTEXT_WINDOW = 8192
CONTEXT_WINDOW_HARD_MIN = 4000
CONTEXT_WINDOW_WARN_BELOW = 8000
CONTEXT_WINDOW_HARD_MIN_RATIO = 0.1
CONTEXT_WINDOW_WARN_BELOW_RATIO = 0.2
SAFETY_MARGIN = 1.2
BASE_CHUNK_RATIO = 0.4
MIN_CHUNK_RATIO = 0.15
SUMMARIZATION_OVERHEAD_TOKENS = 4096

# Priority weights for message retention (higher = keep longer)
PRIORITY_WEIGHTS: dict[str, float] = {
    "system": 100.0,
    "assistant": 1.0,
    "user": 1.5,
    "tool": 0.5,
}


# ===========================================================================
# SQLite schema
# ===========================================================================

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id    TEXT PRIMARY KEY,
    agent_id      TEXT NOT NULL,
    title         TEXT NOT NULL DEFAULT '',
    created_at    REAL NOT NULL,
    updated_at    REAL NOT NULL,
    status        TEXT NOT NULL DEFAULT 'active',
    model         TEXT NOT NULL DEFAULT '',
    context_window INTEGER NOT NULL DEFAULT 8192,
    extra         TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS messages (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    TEXT NOT NULL REFERENCES sessions(session_id),
    role          TEXT NOT NULL,
    content       TEXT NOT NULL,
    timestamp     REAL NOT NULL,
    token_count   INTEGER NOT NULL DEFAULT 0,
    priority      REAL NOT NULL DEFAULT 1.0,
    metadata      TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_ts ON messages(session_id, timestamp);

CREATE TABLE IF NOT EXISTS compaction_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    TEXT NOT NULL REFERENCES sessions(session_id),
    timestamp     REAL NOT NULL,
    tokens_before INTEGER NOT NULL,
    tokens_after  INTEGER NOT NULL,
    strategy      TEXT NOT NULL,
    summary       TEXT
);

CREATE TABLE IF NOT EXISTS audit_events (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    TEXT NOT NULL REFERENCES sessions(session_id),
    timestamp     REAL NOT NULL,
    event_type    TEXT NOT NULL,
    details       TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_audit_events_session ON audit_events(session_id, timestamp DESC);
"""


# ===========================================================================
# SessionManager
# ===========================================================================

class SessionManager:
    """Full session lifecycle backed by SQLite.

    Thread-safe: uses ``check_same_thread=False`` and an ``RLock`` so the
    same instance can be shared across uvicorn worker threads.

    Usage::

        mgr = SessionManager("/path/to/sessions.db")
        sid = mgr.create_session(agent_id="main", model="gpt-4o")
        mgr.append_message(sid, "user", "Hello!")
        history = mgr.get_history(sid)
        mgr.close_session(sid)
    """

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)
        self._conn: sqlite3.Connection | None = None
        self._lock: threading.RLock = threading.RLock()
        self._ensure_connection()

    # -- connection helpers --------------------------------------------------

    def _ensure_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            file_backed = self._db_path != ":memory:"
            if file_backed:
                db_path = Path(self._db_path)
                db_path.parent.mkdir(parents=True, exist_ok=True)
                managed_directory = Path.home() / ".hellochusquis"
                if db_path.parent == managed_directory:
                    os.chmod(managed_directory, 0o700)
            self._conn = sqlite3.connect(
                self._db_path, check_same_thread=False
            )
            if file_backed:
                os.chmod(db_path, 0o600)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.executescript(_SCHEMA_SQL)
        return self._conn

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        with self._lock:
            if self._conn:
                self._conn.close()
                self._conn = None

    # -- session CRUD --------------------------------------------------------

    def create_session(
        self,
        agent_id: str,
        model: str = "",
        context_window: int = DEFAULT_CONTEXT_WINDOW,
        title: str = "",
        extra: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> str:
        """Create a new session, optionally with a stable caller-supplied ID."""
        session_id = session_id or _generate_session_id(agent_id)
        now = time.time()
        with self._lock:
            conn = self._ensure_connection()
            cur = conn.execute(
                """INSERT OR IGNORE INTO sessions
                   (session_id, agent_id, title, created_at, updated_at, status,
                    model, context_window, extra)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    session_id,
                    agent_id,
                    title,
                    now,
                    now,
                    SessionStatus.ACTIVE.value,
                    model,
                    context_window,
                    json.dumps(extra or {}),
                ),
            )
            if cur.rowcount == 0:
                conn.execute(
                    """UPDATE sessions
                       SET updated_at = ?, status = ?, model = ?, context_window = ?
                       WHERE session_id = ?""",
                    (now, SessionStatus.ACTIVE.value, model, context_window, session_id),
                )
            conn.commit()
        return session_id

    def get_session(self, session_id: str) -> SessionMetadata | None:
        """Return metadata for *session_id*, or ``None`` if not found."""
        with self._lock:
            conn = self._ensure_connection()
            row = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
        if row is None:
            return None
        return SessionMetadata(
            session_id=row["session_id"],
            agent_id=row["agent_id"],
            title=row["title"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            status=SessionStatus(row["status"]),
            model=row["model"],
            context_window=row["context_window"],
            extra=json.loads(row["extra"]),
        )

    def list_sessions(
        self,
        agent_id: str | None = None,
        status: SessionStatus | None = None,
        limit: int = 50,
    ) -> list[SessionMetadata]:
        """List sessions with optional filters."""
        with self._lock:
            conn = self._ensure_connection()
            query = "SELECT * FROM sessions WHERE 1=1"
            params: list[Any] = []
            if agent_id:
                query += " AND agent_id = ?"
                params.append(agent_id)
            if status:
                query += " AND status = ?"
                params.append(status.value)
            query += " ORDER BY updated_at DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(query, params).fetchall()
        return [
            SessionMetadata(
                session_id=r["session_id"],
                agent_id=r["agent_id"],
                title=r["title"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
                status=SessionStatus(r["status"]),
                model=r["model"],
                context_window=r["context_window"],
                extra=json.loads(r["extra"]),
            )
            for r in rows
        ]

    def update_session(
        self,
        session_id: str,
        *,
        title: str | None = None,
        model: str | None = None,
        context_window: int | None = None,
        status: SessionStatus | None = None,
        extra: dict[str, Any] | None = None,
    ) -> bool:
        """Update session fields. Returns ``True`` if a row was changed."""
        with self._lock:
            conn = self._ensure_connection()
            serialized_extra = json.dumps(extra) if extra is not None else None
            status_value = status.value if status is not None else None
            cur = conn.execute(
                "UPDATE sessions SET updated_at = ?, title = COALESCE(?, title), "
                "model = COALESCE(?, model), context_window = COALESCE(?, context_window), "
                "status = COALESCE(?, status), extra = COALESCE(?, extra) "
                "WHERE session_id = ?",
                (
                    time.time(),
                    title,
                    model,
                    context_window,
                    status_value,
                    serialized_extra,
                    session_id,
                ),
            )
            conn.commit()
            return cur.rowcount > 0

    def close_session(self, session_id: str) -> bool:
        """Mark session as closed."""
        return self.update_session(session_id, status=SessionStatus.CLOSED)

    def prune_closed_sessions(self, agent_id: str, *, keep: int = 200) -> int:
        """Delete oldest closed sessions for an agent, retaining the newest set."""
        keep = max(0, int(keep))
        with self._lock:
            conn = self._ensure_connection()
            rows = conn.execute(
                """SELECT session_id FROM sessions
                   WHERE agent_id = ? AND status = ?
                   ORDER BY updated_at DESC, session_id DESC
                   LIMIT -1 OFFSET ?""",
                (agent_id, SessionStatus.CLOSED.value, keep),
            ).fetchall()
            session_ids = [row["session_id"] for row in rows]
            for session_id in session_ids:
                conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
                conn.execute("DELETE FROM compaction_log WHERE session_id = ?", (session_id,))
                conn.execute("DELETE FROM audit_events WHERE session_id = ?", (session_id,))
                conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            return len(session_ids)

    def delete_session(self, session_id: str) -> bool:
        """Delete session and all its messages."""
        with self._lock:
            conn = self._ensure_connection()
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM compaction_log WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM audit_events WHERE session_id = ?", (session_id,))
            cur = conn.execute(
                "DELETE FROM sessions WHERE session_id = ?", (session_id,)
            )
            conn.commit()
            return cur.rowcount > 0

    # -- message operations --------------------------------------------------

    def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
        *,
        metadata: dict[str, Any] | None = None,
        priority: float | None = None,
    ) -> int:
        """Append a message and return its auto-increment ID."""
        now = time.time()
        tokens = estimate_tokens(content)
        if priority is None:
            priority = PRIORITY_WEIGHTS.get(role, 1.0)
        with self._lock:
            conn = self._ensure_connection()
            cur = conn.execute(
                """INSERT INTO messages
                   (session_id, role, content, timestamp, token_count, priority, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    session_id,
                    role,
                    content,
                    now,
                    tokens,
                    priority,
                    json.dumps(metadata or {}),
                ),
            )
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                (now, session_id),
            )
            conn.commit()
            return cur.lastrowid or 0  # type: ignore[return-value]

    def get_history(
        self,
        session_id: str,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Return message dicts in chronological order."""
        with self._lock:
            conn = self._ensure_connection()
            query = "SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp ASC"
            params: list[Any] = [session_id]
            if limit is not None:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            rows = conn.execute(query, params).fetchall()
        return [
            {
                "id": r["id"],
                "role": r["role"],
                "content": r["content"],
                "timestamp": r["timestamp"],
                "token_count": r["token_count"],
                "priority": r["priority"],
                "metadata": json.loads(r["metadata"]),
            }
            for r in rows
        ]

    def get_recent_history(self, session_id: str, *, limit: int = 100) -> list[dict[str, Any]]:
        """Return the most recent messages in chronological order."""
        limit = max(1, min(int(limit), 500))
        with self._lock:
            conn = self._ensure_connection()
            rows = conn.execute(
                """SELECT * FROM (
                       SELECT * FROM messages WHERE session_id = ?
                       ORDER BY timestamp DESC, id DESC LIMIT ?
                   ) ORDER BY timestamp ASC, id ASC""",
                (session_id, limit),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "role": row["role"],
                "content": row["content"],
                "timestamp": row["timestamp"],
                "token_count": row["token_count"],
                "priority": row["priority"],
                "metadata": json.loads(row["metadata"]),
            }
            for row in rows
        ]

    def get_history_tokens(self, session_id: str) -> int:
        """Return total token count across all messages in *session_id*."""
        with self._lock:
            conn = self._ensure_connection()
            row = conn.execute(
                "SELECT COALESCE(SUM(token_count), 0) AS total FROM messages WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            return row["total"]  # type: ignore[return-value]

    def delete_message(self, message_id: int) -> bool:
        """Delete a single message by its primary key."""
        with self._lock:
            conn = self._ensure_connection()
            cur = conn.execute("DELETE FROM messages WHERE id = ?", (message_id,))
            conn.commit()
            return cur.rowcount > 0

    def clear_history(self, session_id: str) -> None:
        """Remove all messages for a session."""
        with self._lock:
            conn = self._ensure_connection()
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.commit()

    def replace_history(self, session_id: str, messages: list[dict[str, Any]]) -> None:
        """Swap the full message list atomically (audit #3).

        Compaction used to clear-then-reappend with a commit per message; a
        crash in between truncated the conversation permanently. One
        transaction makes the swap all-or-nothing.
        """
        now = time.time()
        with self._lock:
            conn = self._ensure_connection()
            try:
                conn.execute("BEGIN")
                conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
                for msg in messages:
                    tokens = estimate_tokens(msg.get("content", ""))
                    priority = msg.get("priority") or PRIORITY_WEIGHTS.get(
                        msg.get("role", "user"), 1.0)
                    conn.execute(
                        """INSERT INTO messages
                           (session_id, role, content, timestamp, token_count, priority, metadata)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            session_id,
                            msg.get("role", "user"),
                            msg.get("content", ""),
                            now,
                            tokens,
                            priority,
                            json.dumps(msg.get("metadata") or {}),
                        ),
                    )
                conn.execute(
                    "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                    (now, session_id),
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    # -- audit log -----------------------------------------------------------

    def log_audit_event(
        self,
        session_id: str,
        event_type: str,
        details: dict[str, Any] | None = None,
    ) -> int:
        """Persist a structured, session-scoped audit event."""
        now = time.time()
        with self._lock:
            conn = self._ensure_connection()
            cur = conn.execute(
                """INSERT INTO audit_events (session_id, timestamp, event_type, details)
                   VALUES (?, ?, ?, ?)""",
                (session_id, now, event_type, json.dumps(details or {})),
            )
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                (now, session_id),
            )
            conn.commit()
            return cur.lastrowid or 0  # type: ignore[return-value]

    def list_audit_events(self, session_id: str, *, limit: int = 100) -> list[dict[str, Any]]:
        """Return recent audit events for one session, newest first."""
        limit = max(1, min(int(limit), 200))
        with self._lock:
            conn = self._ensure_connection()
            rows = conn.execute(
                """SELECT id, timestamp, event_type, details
                   FROM audit_events WHERE session_id = ?
                   ORDER BY timestamp DESC, id DESC LIMIT ?""",
                (session_id, limit),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "timestamp": row["timestamp"],
                "event_type": row["event_type"],
                "details": json.loads(row["details"]),
            }
            for row in rows
        ]

    # -- compaction log ------------------------------------------------------

    def log_compaction(
        self,
        session_id: str,
        tokens_before: int,
        tokens_after: int,
        strategy: str,
        summary: str | None = None,
    ) -> None:
        """Record a compaction event."""
        with self._lock:
            conn = self._ensure_connection()
            conn.execute(
                """INSERT INTO compaction_log
                   (session_id, timestamp, tokens_before, tokens_after, strategy, summary)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (session_id, time.time(), tokens_before, tokens_after, strategy, summary),
            )
            conn.commit()

    def get_compaction_history(
        self, session_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Return recent compaction events for *session_id*."""
        with self._lock:
            conn = self._ensure_connection()
            rows = conn.execute(
                """SELECT * FROM compaction_log
                   WHERE session_id = ?
                   ORDER BY timestamp DESC
                   LIMIT ?""",
                (session_id, limit),
            ).fetchall()
        return [
            {
                "id": r["id"],
                "timestamp": r["timestamp"],
                "tokens_before": r["tokens_before"],
                "tokens_after": r["tokens_after"],
                "strategy": r["strategy"],
                "summary": r["summary"],
            }
            for r in rows
        ]


# ===========================================================================
# ConversationCompactor
# ===========================================================================

def _generate_session_id(agent_id: str) -> str:
    """Generate a unique session ID: ``<agent>-<uuid8>``."""
    short_uuid = uuid.uuid4().hex[:12]
    safe_agent = re.sub(r"[^a-zA-Z0-9_-]", "_", agent_id)[:20]
    return f"{safe_agent}-{short_uuid}"
