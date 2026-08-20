"""Deprecated compatibility conversation memory with bounded SQLite access."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

MAX_MEMORY_QUERY_RESULTS = 100


def _bounded_limit(value: object, default: int) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, min(limit, MAX_MEMORY_QUERY_RESULTS))


class ConversationMemory:
    """Enhanced conversation memory with summarization and context."""

    def __init__(self, db_path: str | None = None):
        path = Path(db_path).expanduser() if db_path else Path.home() / ".hellochusquis" / "conversation_memory.db"
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if path.parent != Path("."):
            os.chmod(path.parent, 0o700)
        self.db_path = str(path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, timeout=5)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY,
                    key TEXT UNIQUE,
                    value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    category TEXT DEFAULT 'general'
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS summaries (
                    id INTEGER PRIMARY KEY,
                    session_id TEXT,
                    summary TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    token_count INTEGER
                )
                """
            )
        os.chmod(self.db_path, 0o600)

    def remember(self, key: str, value: str, category: str = "general") -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO memories (key, value, category, accessed_at, access_count)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, 1)
                ON CONFLICT(key) DO UPDATE SET
                    value=excluded.value,
                    category=excluded.category,
                    accessed_at=CURRENT_TIMESTAMP,
                    access_count=memories.access_count + 1
                """,
                (key, value, category),
            )

    def recall(self, key: str) -> str | None:
        with self._connect() as conn:
            conn.execute("UPDATE memories SET accessed_at=CURRENT_TIMESTAMP, access_count=access_count + 1 WHERE key=?", (key,))
            result = conn.execute("SELECT value FROM memories WHERE key=?", (key,)).fetchone()
        return result[0] if result else None

    def forget(self, key: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM memories WHERE key=?", (key,))

    def search(self, query: str, limit: int = 5) -> list[dict]:
        bounded_limit = _bounded_limit(limit, 5)
        with self._connect() as conn:
            results = conn.execute(
                """
                SELECT key, value FROM memories
                WHERE value LIKE ? OR key LIKE ?
                ORDER BY access_count DESC
                LIMIT ?
                """,
                (f"%{query}%", f"%{query}%", bounded_limit),
            ).fetchall()
        return [{"key": key, "value": value} for key, value in results]

    def get_frequent(self, limit: int = 10) -> list[dict]:
        with self._connect() as conn:
            results = conn.execute(
                "SELECT key, value, access_count FROM memories ORDER BY access_count DESC LIMIT ?",
                (_bounded_limit(limit, 10),),
            ).fetchall()
        return [{"key": key, "value": value, "accesses": count} for key, value, count in results]

    def summarize_conversation(self, messages: list) -> str:
        """Summarize a conversation for memory without retaining full content."""
        if not messages:
            return "No conversation to summarize."
        total_chars = sum(len(str(message.get("content", ""))) for message in messages if isinstance(message, dict))
        if total_chars < 200:
            last = messages[-1] if isinstance(messages[-1], dict) else {}
            return str(last.get("content", ""))[:200]
        user_messages = [message for message in messages if isinstance(message, dict) and message.get("role") == "user"]
        assistant_messages = [message for message in messages if isinstance(message, dict) and message.get("role") == "assistant"]
        summary = f"Conversation with {len(user_messages)} user messages and {len(assistant_messages)} assistant responses. "
        if user_messages:
            first = str(user_messages[0].get("content", ""))[:100]
            last = str(user_messages[-1].get("content", ""))[:100]
            summary += f"Started with: '{first}...' Ended with: '{last}...'"
        return summary

    def save_summary(self, session_id: str, summary: str, token_count: int = 0) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO summaries (session_id, summary, token_count) VALUES (?, ?, ?)",
                (session_id, summary, max(0, int(token_count))),
            )

    def get_sessions(self, limit: int = 10) -> list[dict]:
        with self._connect() as conn:
            results = conn.execute(
                "SELECT session_id, summary, created_at FROM summaries ORDER BY created_at DESC LIMIT ?",
                (_bounded_limit(limit, 10),),
            ).fetchall()
        return [{"session": session_id, "summary": summary, "date": created_at} for session_id, summary, created_at in results]


def get_memory() -> ConversationMemory:
    return ConversationMemory()
