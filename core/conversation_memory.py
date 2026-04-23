from __future__ import annotations
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


class ConversationMemory:
    """Enhanced conversation memory with summarization and context."""

    def __init__(self, db_path: str = "memory.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY,
                key TEXT UNIQUE,
                value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                category TEXT DEFAULT 'general'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY,
                session_id TEXT,
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                token_count INTEGER
            )
        """)
        conn.commit()
        conn.close()

    def remember(self, key: str, value: str, category: str = "general"):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO memories (key, value, category, accessed_at, access_count)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, 
                COALESCE((SELECT access_count FROM memories WHERE key = ?), 0) + 1)
        """, (key, value, category, key))
        conn.commit()
        conn.close()

    def recall(self, key: str) -> str | None:
        conn = sqlite3.connect(self.db_path)
        conn.execute("UPDATE memories SET accessed_at = CURRENT_TIMESTAMP, access_count = access_count + 1 WHERE key = ?", (key,))
        conn.commit()
        result = conn.execute("SELECT value FROM memories WHERE key = ?", (key,)).fetchone()
        conn.close()
        return result[0] if result else None

    def forget(self, key: str):
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM memories WHERE key = ?", (key,))
        conn.commit()
        conn.close()

    def search(self, query: str, limit: int = 5) -> list:
        conn = sqlite3.connect(self.db_path)
        results = conn.execute("""
            SELECT key, value FROM memories 
            WHERE value LIKE ? OR key LIKE ?
            ORDER BY access_count DESC
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", limit)).fetchall()
        conn.close()
        return [{"key": k, "value": v} for k, v in results]

    def get_frequent(self, limit: int = 10) -> list:
        conn = sqlite3.connect(self.db_path)
        results = conn.execute("""
            SELECT key, value, access_count FROM memories 
            ORDER BY access_count DESC LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return [{"key": k, "value": v, "accesses": c} for k, v, c in results]

    def summarize_conversation(self, messages: list) -> str:
        """Summarize a conversation for memory."""
        if not messages:
            return "No conversation to summarize."

        total_chars = sum(len(m.get("content", "")) for m in messages)
        if total_chars < 200:
            return messages[-1].get("content", "")[:200] if messages else ""

        user_msgs = [m for m in messages if m.get("role") == "user"]
        assistant_msgs = [m for m in messages if m.get("role") == "assistant"]

        summary = f"Conversation with {len(user_msgs)} user messages and {len(assistant_msgs)} assistant responses. "
        if user_msgs:
            first = user_msgs[0].get("content", "")[:100]
            last = user_msgs[-1].get("content", "")[:100]
            summary += f"Started with: '{first}...' Ended with: '{last}...'"

        return summary

    def save_summary(self, session_id: str, summary: str, token_count: int = 0):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO summaries (session_id, summary, token_count)
            VALUES (?, ?, ?)
        """, (session_id, summary, token_count))
        conn.commit()
        conn.close()

    def get_sessions(self, limit: int = 10) -> list:
        conn = sqlite3.connect(self.db_path)
        results = conn.execute("""
            SELECT session_id, summary, created_at FROM summaries 
            ORDER BY created_at DESC LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return [{"session": s, "summary": m, "date": d} for s, m, d in results]


def get_memory() -> ConversationMemory:
    return ConversationMemory()