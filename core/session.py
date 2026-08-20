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
# Optional tiktoken import
# ---------------------------------------------------------------------------
try:
    import tiktoken as _tiktoken

    _ENCODER = _tiktoken.get_encoding("cl100k_base")
except ImportError:
    _ENCODER = None  # type: ignore[assignment]


# ===========================================================================
# Token estimation helpers
# ===========================================================================

def estimate_tokens(text: str) -> int:
    """Return approximate token count for *text*.

    Uses tiktoken when available, otherwise falls back to ``len(text) // 4``.
    """
    if _ENCODER is not None:
        return len(_ENCODER.encode(text))
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


@dataclass
class ContextWindowInfo:
    """Resolved context-window state."""
    tokens: int
    source: str  # "config" | "model" | "default"
    should_warn: bool = False
    should_block: bool = False
    warn_below: int = 0
    hard_min: int = 0


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
            sets: list[str] = ["updated_at = ?"]
            params: list[Any] = [time.time()]
            if title is not None:
                sets.append("title = ?")
                params.append(title)
            if model is not None:
                sets.append("model = ?")
                params.append(model)
            if context_window is not None:
                sets.append("context_window = ?")
                params.append(context_window)
            if status is not None:
                sets.append("status = ?")
                params.append(status.value)
            if extra is not None:
                sets.append("extra = ?")
                params.append(json.dumps(extra))
            params.append(session_id)
            cur = conn.execute(
                f"UPDATE sessions SET {', '.join(sets)} WHERE session_id = ?",
                params,
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

class CompactionStrategy(str, Enum):
    """Built-in compaction strategies."""
    RECENT_KEEP = "recent_keep"       # keep N most recent, summarize rest
    PRIORITY_BASED = "priority_based" # drop low-priority first
    AGGRESSIVE = "aggressive"         # summarize everything possible
    NONE = "none"                     # no compaction


class ConversationCompactor:
    """    Smart conversation compaction to fit context windows.

    Python-native implementation.  Supports multiple strategies, priority-based retention,
    chunked summarization, and oversized-message fallback.

    Usage::

        compactor = ConversationCompactor()
        result = compactor.compact(messages, max_tokens=4000)
    """

    def __init__(
        self,
        *,
        safety_margin: float = SAFETY_MARGIN,
        base_chunk_ratio: float = BASE_CHUNK_RATIO,
        min_chunk_ratio: float = MIN_CHUNK_RATIO,
    ) -> None:
        self.safety_margin = safety_margin
        self.base_chunk_ratio = base_chunk_ratio
        self.min_chunk_ratio = min_chunk_ratio

    # -- public API ----------------------------------------------------------

    def compact(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int,
        *,
        strategy: CompactionStrategy = CompactionStrategy.RECENT_KEEP,
        keep_recent: int = 6,
        summarize_fn: Callable[[list[dict[str, Any]]], str] | None = None,
        system_message: dict[str, Any] | None = None,
    ) -> CompactionResult:
        """Compact *messages* to fit within *max_tokens*.

        Parameters
        ----------
        messages:
            Full conversation history (role/content dicts).
        max_tokens:
            Target token budget after compaction.
        strategy:
            Which compaction strategy to apply.
        keep_recent:
            Number of most-recent messages to preserve verbatim
            (used by ``RECENT_KEEP``).
        summarize_fn:
            Optional callable that receives a list of messages and returns a
            summary string.  When ``None``, messages are dropped with a note.
        system_message:
            If provided, always kept at position 0.

        Returns
        -------
        CompactionResult
        """
        total_before = estimate_messages_tokens(messages)
        if total_before <= max_tokens:
            return CompactionResult(
                messages=list(messages),
                tokens_before=total_before,
                tokens_after=total_before,
                strategy_used=CompactionStrategy.NONE.value,
                dropped_count=0,
            )

        if strategy == CompactionStrategy.NONE:
            return CompactionResult(
                messages=list(messages),
                tokens_before=total_before,
                tokens_after=total_before,
                strategy_used=CompactionStrategy.NONE.value,
                dropped_count=0,
            )

        # Separate system message if present
        sys_msg: dict[str, Any] | None = system_message
        conversation = list(messages)
        if not sys_msg and conversation and conversation[0].get("role") == "system":
            sys_msg = conversation.pop(0)

        if strategy == CompactionStrategy.RECENT_KEEP:
            compacted, dropped, summary = self._strategy_recent_keep(
                conversation, max_tokens, keep_recent, summarize_fn
            )
        elif strategy == CompactionStrategy.PRIORITY_BASED:
            compacted, dropped, summary = self._strategy_priority_based(
                conversation, max_tokens, summarize_fn
            )
        elif strategy == CompactionStrategy.AGGRESSIVE:
            compacted, dropped, summary = self._strategy_aggressive(
                conversation, max_tokens, summarize_fn
            )
        else:
            compacted, dropped, summary = conversation, 0, None

        # Re-insert system message
        if sys_msg is not None:
            compacted = [sys_msg] + compacted

        total_after = estimate_messages_tokens(compacted)
        return CompactionResult(
            messages=compacted,
            tokens_before=total_before,
            tokens_after=total_after,
            strategy_used=strategy.value,
            dropped_count=dropped,
            summary_text=summary,
        )

    def compute_adaptive_chunk_ratio(
        self,
        messages: Sequence[dict[str, Any]],
        context_window: int,
    ) -> float:
        """Compute adaptive chunk ratio based on average message size.
        """
        if not messages:
            return self.base_chunk_ratio
        avg_tokens = estimate_messages_tokens(messages) / len(messages)
        avg_ratio = (avg_tokens * self.safety_margin) / context_window
        if avg_ratio > 0.1:
            reduction = min(avg_ratio * 2, self.base_chunk_ratio - self.min_chunk_ratio)
            return max(self.min_chunk_ratio, self.base_chunk_ratio - reduction)
        return self.base_chunk_ratio

    def is_oversized(
        self, message: dict[str, Any], context_window: int
    ) -> bool:
        """Check whether a single message exceeds 50% of *context_window*."""
        tokens = estimate_message_tokens(message) * self.safety_margin
        return tokens > context_window * 0.5

    def build_summary_chunks(
        self,
        messages: Sequence[dict[str, Any]],
        max_chunk_tokens: int,
    ) -> list[list[dict[str, Any]]]:
        """Split *messages* into chunks suitable for summarization.

        Groups consecutive tool-call/result pairs to avoid splitting them.
        """
        effective_max = max(1, int(max_chunk_tokens / self.safety_margin))
        groups = self._group_messages(list(messages))
        chunks: list[list[dict[str, Any]]] = []
        current: list[dict[str, Any]] = []
        current_tokens = 0
        for group in groups:
            group_tokens = estimate_messages_tokens(group)
            if current and current_tokens + group_tokens > effective_max:
                chunks.append(current)
                current = []
                current_tokens = 0
            current.extend(group)
            current_tokens += group_tokens
        if current:
            chunks.append(current)
        return chunks

    # -- private strategies --------------------------------------------------

    def _strategy_recent_keep(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int,
        keep_recent: int,
        summarize_fn: Callable[[list[dict[str, Any]]], str] | None,
    ) -> tuple[list[dict[str, Any]], int, str | None]:
        """Keep the last *keep_recent* messages verbatim; summarize/drop the rest."""
        if len(messages) <= keep_recent:
            return messages, 0, None

        tail = messages[-keep_recent:]
        middle = messages[:-keep_recent]
        tail_tokens = estimate_messages_tokens(tail)
        budget = max_tokens - tail_tokens

        if budget <= 0:
            # Even the tail is too large; trim it
            return self._trim_to_budget(messages, max_tokens), len(messages) - keep_recent, None

        # Try to fit summarized middle
        if summarize_fn:
            summary_text = summarize_fn(middle)
            summary_msg = {"role": "system", "content": f"[Summary]\n{summary_text}"}
            summary_tokens = estimate_message_tokens(summary_msg)
            if summary_tokens <= budget:
                return [summary_msg] + tail, len(middle), summary_text

        # No summarize fn or summary too large: drop middle entirely
        drop_note = f"[{len(middle)} messages compressed — {estimate_messages_tokens(middle)} tokens]"
        return tail, len(middle), drop_note

    def _strategy_priority_based(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int,
        summarize_fn: Callable[[list[dict[str, Any]]], str] | None,
    ) -> tuple[list[dict[str, Any]], int, str | None]:
        """Drop lowest-priority messages until budget is met."""
        scored = [
            (m, m.get("priority", PRIORITY_WEIGHTS.get(m.get("role", ""), 1.0)), i)
            for i, m in enumerate(messages)
        ]
        # Sort by priority (ascending) — lowest first to drop
        scored.sort(key=lambda x: (x[1], x[2]))

        kept = list(messages)
        dropped = 0
        total = estimate_messages_tokens(kept)
        while total > max_tokens and scored:
            item = scored.pop(0)
            msg, _, _ = item
            if msg.get("role") == "system":
                continue  # never drop system messages
            if msg in kept:
                kept.remove(msg)
                total = estimate_messages_tokens(kept)
                dropped += 1

        summary = None
        if dropped > 0 and summarize_fn:
            # Build a summary of what was dropped
            dropped_msgs = [m for m in messages if m not in kept]
            if dropped_msgs:
                summary = summarize_fn(dropped_msgs)

        return kept, dropped, summary

    def _strategy_aggressive(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int,
        summarize_fn: Callable[[list[dict[str, Any]]], str] | None,
    ) -> tuple[list[dict[str, Any]], int, str | None]:
        """Aggressively summarize in chunks until budget is met."""
        chunks = self.build_summary_chunks(messages, max_tokens // 2)
        summaries: list[str] = []
        total_dropped = 0

        # First pass: try to summarize each chunk
        kept_chunks: list[list[dict[str, Any]]] = []
        for chunk in chunks:
            chunk_tokens = estimate_messages_tokens(chunk)
            if chunk_tokens <= max_tokens // max(len(chunks), 1):
                if summarize_fn:
                    summaries.append(summarize_fn(chunk))
                    total_dropped += len(chunk)
                else:
                    kept_chunks.append(chunk)
            else:
                # Even the chunk is too big; trim it
                kept_chunks.append(self._trim_to_budget(chunk, max_tokens // max(len(chunks), 1)))

        # Build result
        result: list[dict[str, Any]] = []
        if summaries:
            combined_summary = "\n\n".join(summaries)
            result.append({
                "role": "system",
                "content": f"[Conversation Summary]\n{combined_summary}",
            })
        for chunk in kept_chunks:
            result.extend(chunk)

        return result, total_dropped, "\n\n".join(summaries) if summaries else None

    # -- helpers -------------------------------------------------------------

    def _trim_to_budget(
        self, messages: list[dict[str, Any]], max_tokens: int
    ) -> list[dict[str, Any]]:
        """Keep as many recent messages as fit within *max_tokens*."""
        result: list[dict[str, Any]] = []
        total = 0
        for msg in reversed(messages):
            t = estimate_message_tokens(msg)
            if total + t > max_tokens:
                break
            result.append(msg)
            total += t
        result.reverse()
        return result

    @staticmethod
    def _group_messages(
        messages: list[dict[str, Any]],
    ) -> list[list[dict[str, Any]]]:
        """Group consecutive tool-call/result messages into atomic units."""
        groups: list[list[dict[str, Any]]] = []
        current: list[dict[str, Any]] = []
        pending_tool_ids: set[str] = set()

        for msg in messages:
            current.append(msg)
            role = msg.get("role", "")

            if role == "assistant":
                # Extract tool call IDs from content (simple heuristic)
                content = msg.get("content", "")
                if isinstance(content, str):
                    ids = re.findall(r'"id"\s*:\s*"([^"]+)"', content)
                    pending_tool_ids = set(ids)
            elif role == "tool":
                tool_id = msg.get("tool_call_id", msg.get("metadata", {}).get("tool_call_id", ""))
                if tool_id and tool_id in pending_tool_ids:
                    pending_tool_ids.discard(tool_id)

            if not pending_tool_ids:
                groups.append(current)
                current = []
                pending_tool_ids = set()

        if current:
            groups.append(current)
        return groups


# ===========================================================================
# ContextWindowGuard
# ===========================================================================

class ContextWindowGuard:
    """Monitor token usage against model limits and auto-trigger compaction.

    Usage::

        guard = ContextWindowGuard(context_window=128_000)
        info = guard.check(current_tokens=110_000)
        if info.should_warn:
            print(f"Warning: {info.warn_below} threshold")
    """

    def __init__(
        self,
        *,
        context_window: int = DEFAULT_CONTEXT_WINDOW,
        hard_min: int | None = None,
        warn_below: int | None = None,
        source: str = "default",
    ) -> None:
        self._raw_context_window = context_window
        self._source = source

        # Compute thresholds from reference window
        ref = context_window
        self._hard_min = hard_min or max(
            CONTEXT_WINDOW_HARD_MIN,
            int(ref * CONTEXT_WINDOW_HARD_MIN_RATIO),
        )
        self._warn_below = warn_below or max(
            CONTEXT_WINDOW_WARN_BELOW,
            int(ref * CONTEXT_WINDOW_WARN_BELOW_RATIO),
        )

    @classmethod
    def from_config(
        cls,
        *,
        model_context_tokens: int | None = None,
        agent_context_tokens: int | None = None,
        config_context_tokens: int | None = None,
        default_tokens: int = DEFAULT_CONTEXT_WINDOW,
    ) -> ContextWindowInfo:
        """Resolve effective context window from layered config values.
        """
        base = config_context_tokens or model_context_tokens or default_tokens
        source = "default"
        if config_context_tokens:
            source = "config"
        elif model_context_tokens:
            source = "model"

        # Agent-level cap
        effective = base
        if agent_context_tokens and agent_context_tokens < base:
            effective = agent_context_tokens
            source = "agent_cap"

        return ContextWindowInfo(
            tokens=effective,
            source=source,
        )

    def check(self, current_tokens: int) -> ContextWindowInfo:
        """Evaluate current token usage and return guard status."""
        threshold = max(
            CONTEXT_WINDOW_HARD_MIN,
            int(self._raw_context_window * CONTEXT_WINDOW_HARD_MIN_RATIO),
        )
        warn_threshold = max(
            CONTEXT_WINDOW_WARN_BELOW,
            int(self._raw_context_window * CONTEXT_WINDOW_WARN_BELOW_RATIO),
        )

        return ContextWindowInfo(
            tokens=self._raw_context_window,
            source=self._source,
            should_warn=current_tokens < warn_threshold or self._raw_context_window < warn_threshold,
            should_block=self._raw_context_window < threshold,
            warn_below=warn_threshold,
            hard_min=threshold,
        )

    def should_compact(self, current_tokens: int) -> bool:
        """Return ``True`` if current usage is approaching the context limit."""
        usable = int(self._raw_context_window * 0.85)  # 85% target
        return current_tokens > usable

    def budget_for_history(
        self,
        system_tokens: int = 0,
        response_reserve: int = 2048,
        history_share: float = 0.7,
    ) -> int:
        """Compute the token budget available for conversation history."""
        available = self._raw_context_window - system_tokens - response_reserve
        return max(1, int(available * history_share))

    def format_warning(self, model_id: str = "unknown") -> str:
        """Format a human-readable warning about context window size."""
        return (
            f"Context window is small: {model_id} "
            f"ctx={self._raw_context_window} "
            f"(warn<{self._warn_below}) "
            f"source={self._source}"
        )

    def format_block(self) -> str:
        """Format a blocking message when context window is too small."""
        return (
            f"Model context window too small "
            f"({self._raw_context_window} tokens; "
            f"source={self._source}). "
            f"Minimum is {self._hard_min}."
        )


# ===========================================================================
# PromptComposer
# ===========================================================================

class PromptComposer:
    """Compose system prompts from identity, memory, context, and tools.

    Usage::

        composer = PromptComposer()
        prompt = composer.compose(
            identity="You are a helpful assistant.",
            memory="User prefers Spanish.",
            tools=[{"name": "read", "summary": "Read files"}],
            context_files=[{"path": "AGENTS.md", "content": "..."}],
        )
    """

    def __init__(self) -> None:
        self._sections: list[str] = []
        self._templates: dict[str, str] = {}

    # -- template system -----------------------------------------------------

    def register_template(self, name: str, template: str) -> None:
        """Register a named prompt template with ``{variable}`` placeholders."""
        self._templates[name] = template

    def render_template(
        self, name: str, variables: dict[str, str] | None = None
    ) -> str:
        """Render a registered template with the given variables."""
        tpl = self._templates.get(name)
        if tpl is None:
            raise KeyError(f"Template '{name}' not registered")
        if variables:
            return tpl.format(**variables)
        return tpl

    # -- section builders ----------------------------------------------------

    @staticmethod
    def build_identity_section(identity: str) -> str:
        """Render the identity/base-personality section."""
        return identity.strip()

    @staticmethod
    def build_memory_section(memory: str) -> str:
        """Render the memory/durable-facts section."""
        if not memory.strip():
            return ""
        return f"## Memory\n\n{memory.strip()}"

    @staticmethod
    def build_tools_section(
        tools: Sequence[dict[str, str]],
        *,
        read_tool_name: str = "read",
    ) -> str:
        """Render the available-tools section."""
        if not tools:
            return ""
        lines = ["## Tools", ""]
        for tool in tools:
            name = tool.get("name", "unknown")
            summary = tool.get("summary", "")
            if summary:
                lines.append(f"- {name}: {summary}")
            else:
                lines.append(f"- {name}")
        lines.append("")
        lines.append(
            f"Use `{read_tool_name}` to read tool documentation when needed."
        )
        return "\n".join(lines)

    @staticmethod
    def build_context_files_section(
        files: Sequence[dict[str, str]],
        *,
        heading: str = "# Project Context",
        dynamic: bool = False,
    ) -> str:
        """Render embedded context files (AGENTS.md, memory.md, etc.)."""
        if not files:
            return ""
        lines = [heading, ""]
        if dynamic:
            lines.append("Frequently-changing files:")
            lines.append("")
        for f in files:
            path = f.get("path", "unknown")
            content = f.get("content", "")
            lines.extend([f"## {path}", "", content, ""])
        return "\n".join(lines)

    @staticmethod
    def build_runtime_section(
        *,
        agent_id: str = "",
        session_id: str = "",
        model: str = "",
        host: str = "",
        os_info: str = "",
        shell: str = "",
        channel: str = "",
        thinking: str = "off",
    ) -> str:
        """Render the runtime-info line."""
        parts = []
        if agent_id:
            parts.append(f"agent={agent_id}")
        if session_id:
            parts.append(f"session={session_id}")
        if model:
            parts.append(f"model={model}")
        if host:
            parts.append(f"host={host}")
        if os_info:
            parts.append(f"os={os_info}")
        if shell:
            parts.append(f"shell={shell}")
        if channel:
            parts.append(f"channel={channel}")
        parts.append(f"thinking={thinking}")
        joined = " | ".join(p for p in parts if p)
        return f"## Runtime\n\n{joined}"

    @staticmethod
    def build_temporal_section(
        *, date: str = "", timezone: str = ""
    ) -> str:
        """Render temporal context (current date/timezone)."""
        if not date and not timezone:
            return ""
        lines = ["## Temporal Context", ""]
        if date:
            lines.append(f"Current date: {date}")
        if timezone:
            lines.append(f"Time zone: {timezone}")
        return "\n".join(lines)

    @staticmethod
    def build_safety_section() -> str:
        """Render the safety directives section."""
        return textwrap.dedent("""\
            ## Safety

            No independent goals, self-preservation, replication, resource
            acquisition, power-seeking, or plans beyond user request.
            Safety/oversight > completion. Conflict: pause/ask.
            Obey stop/pause/audit; never bypass safeguards.
        """)

    @staticmethod
    def build_execution_bias_section() -> str:
        """Render the execution-bias section."""
        return textwrap.dedent("""\
            ## Execution Bias

            - Actionable request: act now.
            - Non-final turn: advance with tools, or ask one safety-blocking decision.
            - Continue to done/real blocker; no plan-only finish when tools can act.
            - Weak/empty result: vary query/path/command/source, then conclude.
            - Mutable facts: live-check files/git/time/versions/services.
            - Final claim needs evidence or named blocker.
        """)

    @staticmethod
    def build_compacted_history_section(summary: str) -> str:
        """Render a compacted-history placeholder."""
        if not summary:
            return ""
        return f"## Prior Conversation Summary\n\n{summary}"

    # -- main compose --------------------------------------------------------

    def compose(
        self,
        *,
        identity: str = "You are a helpful assistant.",
        memory: str = "",
        extra_prompt: str = "",
        tools: Sequence[dict[str, str]] | None = None,
        context_files: Sequence[dict[str, str]] | None = None,
        dynamic_context_files: Sequence[dict[str, str]] | None = None,
        runtime_info: dict[str, str] | None = None,
        temporal_info: dict[str, str] | None = None,
        compacted_summary: str = "",
        include_safety: bool = True,
        include_execution_bias: bool = True,
        read_tool_name: str = "read",
    ) -> str:
        """Compose the full system prompt from all sections.

        Parameters
        ----------
        identity:
            Base identity / personality line.
        memory:
            Durable memory / user preferences.
        extra_prompt:
            Additional conversation context injected by the caller.
        tools:
            List of ``{"name": ..., "summary": ...}`` dicts.
        context_files:
            Stable project-context files (AGENTS.md, etc.).
        dynamic_context_files:
            Frequently-changing context files.
        runtime_info:
            Dict of runtime metadata (agent_id, model, host, etc.).
        temporal_info:
            Dict with ``date`` and ``timezone`` keys.
        compacted_summary:
            Summary of prior conversation (from compaction).
        include_safety:
            Whether to include the safety section.
        include_execution_bias:
            Whether to include the execution-bias section.
        read_tool_name:
            Name of the file-reading tool for the current runtime.

        Returns
        -------
        str
            The assembled system prompt.
        """
        sections: list[str] = []

        # 1. Identity (always first)
        sections.append(self.build_identity_section(identity))

        # 2. Memory
        mem = self.build_memory_section(memory)
        if mem:
            sections.append(mem)

        # 3. Tools
        if tools:
            sections.append(self.build_tools_section(tools, read_tool_name=read_tool_name))

        # 4. Context files (stable)
        if context_files:
            sections.append(self.build_context_files_section(context_files))

        # 5. Compacted history summary
        if compacted_summary:
            sections.append(self.build_compacted_history_section(compacted_summary))

        # 6. Execution bias
        if include_execution_bias:
            sections.append(self.build_execution_bias_section())

        # 7. Safety
        if include_safety:
            sections.append(self.build_safety_section())

        # 8. Temporal context
        if temporal_info:
            ts = self.build_temporal_section(
                date=temporal_info.get("date", ""),
                timezone=temporal_info.get("timezone", ""),
            )
            if ts:
                sections.append(ts)

        # 9. Dynamic context files
        if dynamic_context_files:
            sections.append(
                self.build_context_files_section(
                    dynamic_context_files,
                    heading="# Dynamic Project Context",
                    dynamic=True,
                )
            )

        # 10. Runtime info
        if runtime_info:
            rt = self.build_runtime_section(
                agent_id=runtime_info.get("agent_id", ""),
                session_id=runtime_info.get("session_id", ""),
                model=runtime_info.get("model", ""),
                host=runtime_info.get("host", ""),
                os_info=runtime_info.get("os", ""),
                shell=runtime_info.get("shell", ""),
                channel=runtime_info.get("channel", ""),
                thinking=runtime_info.get("thinking", "off"),
            )
            sections.append(rt)

        # 11. Extra prompt
        if extra_prompt.strip():
            sections.append(f"## Additional Context\n\n{extra_prompt.strip()}")

        return "\n\n".join(s for s in sections if s)


# ===========================================================================
# High-level integration: AutoCompactingSession
# ===========================================================================

class AutoCompactingSession:
    """Convenience class that ties SessionManager, ConversationCompactor,
    ContextWindowGuard, and PromptComposer together.

    Usage::

        session = AutoCompactingSession(
            db_path="sessions.db",
            agent_id="main",
            model="gpt-4o",
            context_window=128_000,
        )
        session.start()

        # Use in your agent loop:
        session.append("user", "Hello!")
        messages = session.get_compacted_history()
        system_prompt = session.build_system_prompt(identity="...")

        session.end()
    """

    def __init__(
        self,
        *,
        db_path: str | Path,
        agent_id: str,
        model: str = "",
        context_window: int = DEFAULT_CONTEXT_WINDOW,
        max_history_tokens: int | None = None,
        compaction_strategy: CompactionStrategy = CompactionStrategy.RECENT_KEEP,
        keep_recent: int = 6,
        summarize_fn: Callable[[list[dict[str, Any]]], str] | None = None,
        title: str = "",
    ) -> None:
        self._mgr = SessionManager(db_path)
        self._compactor = ConversationCompactor()
        self._guard = ContextWindowGuard(context_window=context_window, source="config")
        self._composer = PromptComposer()

        self.agent_id = agent_id
        self.model = model
        self.context_window = context_window
        self.max_history_tokens = max_history_tokens or self._guard.budget_for_history()
        self.compaction_strategy = compaction_strategy
        self.keep_recent = keep_recent
        self.summarize_fn = summarize_fn

        self.session_id: str = ""
        self.title = title

    def start(self) -> str:
        """Create (or resume) the session. Returns the session ID."""
        if not self.session_id:
            self.session_id = self._mgr.create_session(
                agent_id=self.agent_id,
                model=self.model,
                context_window=self.context_window,
                title=self.title,
            )
        return self.session_id

    def end(self) -> None:
        """Close the session."""
        if self.session_id:
            self._mgr.close_session(self.session_id)

    def append(
        self,
        role: str,
        content: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Append a message and auto-compact if needed."""
        msg_id = self._mgr.append_message(
            self.session_id, role, content, metadata=metadata
        )
        # Auto-compact check
        total = self._mgr.get_history_tokens(self.session_id)
        if self._guard.should_compact(total):
            self._do_compact()
        return msg_id

    def get_history(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Return raw (uncompacted) history."""
        return self._mgr.get_history(self.session_id, **kwargs)

    def get_compacted_history(self) -> list[dict[str, Any]]:
        """Return history compacted to fit the context window."""
        messages = self._mgr.get_history(self.session_id)
        total = estimate_messages_tokens(messages)
        if total <= self.max_history_tokens:
            return messages

        result = self._compactor.compact(
            messages,
            self.max_history_tokens,
            strategy=self.compaction_strategy,
            keep_recent=self.keep_recent,
            summarize_fn=self.summarize_fn,
        )

        # Persist compaction log
        self._mgr.log_compaction(
            self.session_id,
            result.tokens_before,
            result.tokens_after,
            result.strategy_used,
            result.summary_text,
        )

        return result.messages

    def build_system_prompt(self, **kwargs: Any) -> str:
        """Build a system prompt via the PromptComposer."""
        return self._composer.compose(**kwargs)

    @property
    def manager(self) -> SessionManager:
        """Direct access to the underlying SessionManager."""
        return self._mgr

    @property
    def compactor(self) -> ConversationCompactor:
        """Direct access to the underlying ConversationCompactor."""
        return self._compactor

    @property
    def guard(self) -> ContextWindowGuard:
        """Direct access to the underlying ContextWindowGuard."""
        return self._guard

    @property
    def composer(self) -> PromptComposer:
        """Direct access to the underlying PromptComposer."""
        return self._composer

    def _do_compact(self) -> CompactionResult:
        """Internal: run compaction and persist the result."""
        messages = self._mgr.get_history(self.session_id)
        result = self._compactor.compact(
            messages,
            self.max_history_tokens,
            strategy=self.compaction_strategy,
            keep_recent=self.keep_recent,
            summarize_fn=self.summarize_fn,
        )

        # Persist: clear old, write compacted
        self._mgr.clear_history(self.session_id)
        for msg in result.messages:
            self._mgr.append_message(
                self.session_id,
                msg.get("role", "user"),
                msg.get("content", ""),
                metadata=msg.get("metadata"),
                priority=msg.get("priority"),
            )

        self._mgr.log_compaction(
            self.session_id,
            result.tokens_before,
            result.tokens_after,
            result.strategy_used,
            result.summary_text,
        )
        return result


# ===========================================================================
# Internal helpers
# ===========================================================================

def _generate_session_id(agent_id: str) -> str:
    """Generate a unique session ID: ``<agent>-<uuid8>``."""
    short_uuid = uuid.uuid4().hex[:12]
    safe_agent = re.sub(r"[^a-zA-Z0-9_-]", "_", agent_id)[:20]
    return f"{safe_agent}-{short_uuid}"
