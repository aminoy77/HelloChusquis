import json
from pathlib import Path
from datetime import datetime
from rich.console import Console

console = Console()

LEARNING_DIR = Path.home() / ".hellochusquis"
LEARNING_FILE = LEARNING_DIR / "learnings.json"


def init():
    LEARNING_DIR.mkdir(exist_ok=True)
    if not LEARNING_FILE.exists():
        LEARNING_FILE.write_text(json.dumps({
            "tool_patterns": {},
            "errors": [],
            "system_prompt_improvements": [],
            "feedback": {"positive": [], "negative": []},
            "updated_at": None,
        }, indent=2))


def load_learnings() -> dict:
    init()
    return json.loads(LEARNING_FILE.read_text())


def save_learnings(data: dict):
    init()
    data["updated_at"] = datetime.now().isoformat()
    LEARNING_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


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


def add_feedback(feedback_type: str, context: str):
    learnings = load_learnings()
    entry = {"context": context[:200], "timestamp": datetime.now().isoformat()}
    if "feedback" not in learnings:
        learnings["feedback"] = {"positive": [], "negative": []}
    if feedback_type not in learnings["feedback"]:
        learnings["feedback"][feedback_type] = []
    learnings["feedback"][feedback_type].append(entry)
    # Mantén máximo 50 entradas de feedback
    learnings["feedback"][feedback_type] = learnings["feedback"][feedback_type][-50:]
    save_learnings(learnings)


def analyze_and_learn(messages: list[dict], pool) -> None:
    if not messages or len(messages) < 2:
        return

    conversation = "\n".join(
        f"{m['role']}: {m['content'][:300]}"
        for m in messages
        if m.get('content')
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
                )
            },
            {
                "role": "user",
                "content": f"Analyze this conversation:\n\n{conversation}"
            }
        ])

        choices = response.get("choices", [])
        if not choices:
            return
        content = choices[0].get("message", {}).get("content", "").strip()
        content = content.replace("```json", "").replace("```", "").strip()
        new_learnings = json.loads(content)

        learnings = load_learnings()

        # Merge tool patterns
        for task, tools in new_learnings.get("tool_patterns", {}).items():
            if task not in learnings["tool_patterns"]:
                learnings["tool_patterns"][task] = []
            for tool in tools:
                if tool not in learnings["tool_patterns"][task]:
                    learnings["tool_patterns"][task].append(tool)

        # Merge errors — máximo 20
        for error in new_learnings.get("errors", []):
            if error not in learnings["errors"]:
                learnings["errors"].append(error)
        learnings["errors"] = learnings["errors"][-20:]

        # Merge improvements — máximo 20
        for imp in new_learnings.get("improvements", []):
            if imp not in learnings["system_prompt_improvements"]:
                learnings["system_prompt_improvements"].append(imp)
        learnings["system_prompt_improvements"] = learnings["system_prompt_improvements"][-20:]

        save_learnings(learnings)
        console.print("[dim]✓ Learnings updated.[/dim]")

    except Exception:
        pass  # Si falla el análisis no pasa nada