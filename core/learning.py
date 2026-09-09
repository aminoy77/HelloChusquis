"""Bounded, thread-safe persistence for local agent learnings and feedback."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
import tempfile
import threading

from rich.console import Console

console = Console()

LEARNING_DIR = Path.home() / ".hellochusquis"
LEARNING_FILE = LEARNING_DIR / "learnings.json"
_LEARNING_LOCK = threading.RLock()


def _empty_learnings() -> dict:
    return {
        "tool_patterns": {},
        "errors": [],
        "system_prompt_improvements": [],
        "feedback": {"positive": [], "negative": []},
        "updated_at": None,
    }


def _secure_storage_dir() -> None:
    LEARNING_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(LEARNING_DIR, 0o700)


def _write_atomically(data: dict) -> None:
    """Write JSON through a same-directory temporary file then replace it."""
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{LEARNING_FILE.name}.",
        suffix=".tmp",
        dir=LEARNING_DIR,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_name, 0o600)
        os.replace(temporary_name, LEARNING_FILE)
        os.chmod(LEARNING_FILE, 0o600)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def init() -> None:
    """Initialize owner-only learning storage exactly once."""
    with _LEARNING_LOCK:
        _secure_storage_dir()
        if not LEARNING_FILE.exists():
            _write_atomically(_empty_learnings())
        else:
            os.chmod(LEARNING_FILE, 0o600)


def load_learnings() -> dict:
    """Load learnings from the protected local JSON store."""
    with _LEARNING_LOCK:
        init()
        return json.loads(LEARNING_FILE.read_text(encoding="utf-8"))


def save_learnings(data: dict) -> None:
    """Atomically replace local learnings after a complete serialization."""
    with _LEARNING_LOCK:
        _secure_storage_dir()
        data["updated_at"] = datetime.now().isoformat()
        _write_atomically(data)


def build_learning_prompt(learnings: dict) -> str:
    parts = []

    if learnings.get("tool_patterns"):
        parts.append("TOOL PATTERNS (what worked before):")
        for task, tools in learnings["tool_patterns"].items():
            parts.append(f"  - For '{task}': use {', '.join(tools)}")

    if learnings.get("errors"):
        parts.append("\nMISTAKES TO AVOID:")
        for error in learnings["errors"][-10:]:
            parts.append(f"  - {error}")

    if learnings.get("system_prompt_improvements"):
        parts.append("\nLEARNED RULES:")
        for rule in learnings["system_prompt_improvements"][-10:]:
            parts.append(f"  - {rule}")

    return "\n".join(parts) if parts else ""


def add_feedback(feedback_type: str, context: str) -> None:
    """Append bounded feedback without losing concurrent updates."""
    with _LEARNING_LOCK:
        learnings = load_learnings()
        entry = {"context": context[:200], "timestamp": datetime.now().isoformat()}
        feedback = learnings.setdefault("feedback", {"positive": [], "negative": []})
        feedback.setdefault(feedback_type, []).append(entry)
        feedback[feedback_type] = feedback[feedback_type][-50:]
        save_learnings(learnings)


def analyze_and_learn(messages: list[dict], pool) -> None:
    if not messages or len(messages) < 2:
        return

    conversation = "\n".join(
        f"{message['role']}: {message['content'][:300]}"
        for message in messages
        if message.get("content")
    )

    try:
        response = pool.chat_with_retry([
            {
                "role": "system",
                "content": (
                    "You are a learning analyzer for an AI agent. "
                    "Analyze this conversation and extract learnings. "
                    "Respond ONLY with a JSON object with these keys:\n"
                    "- tool_patterns: dict of {task_type: [tools_that_worked]}\n"
                    "- errors: list of mistakes made (max 3)\n"
                    "- improvements: list of rules to improve future behavior (max 3)\n"
                    "Keep all strings short and actionable. "
                    "Respond ONLY with valid JSON, no markdown."
                ),
            },
            {
                "role": "user",
                "content": f"Analyze this conversation:\n\n{conversation}",
            },
        ])

        choices = response.get("choices", [])
        if not choices:
            return
        content = choices[0].get("message", {}).get("content", "").strip()
        content = content.replace("```json", "").replace("```", "").strip()
        new_learnings = json.loads(content)

        with _LEARNING_LOCK:
            learnings = load_learnings()

            for task, tools in new_learnings.get("tool_patterns", {}).items():
                existing_tools = learnings.setdefault("tool_patterns", {}).setdefault(task, [])
                for tool in tools:
                    if tool not in existing_tools:
                        existing_tools.append(tool)

            errors = learnings.setdefault("errors", [])
            for error in new_learnings.get("errors", []):
                if error not in errors:
                    errors.append(error)
            learnings["errors"] = errors[-20:]

            improvements = learnings.setdefault("system_prompt_improvements", [])
            for improvement in new_learnings.get("improvements", []):
                if improvement not in improvements:
                    improvements.append(improvement)
            learnings["system_prompt_improvements"] = improvements[-20:]

            save_learnings(learnings)
        console.print("[dim]✓ Learnings updated.[/dim]")

    except Exception:
        pass  # Learning extraction must not disrupt the primary agent turn.
