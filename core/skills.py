"""Reusable skill registry with approval-gated, bounded local actions."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shlex
import subprocess
from dataclasses import dataclass, field
from typing import Any


SKILL_ACTION_TIMEOUT_SECONDS = 60
SKILL_ACTION_OUTPUT_MAX_CHARS = 65_536
_SAFE_ENVIRONMENT_KEYS = ("HOME", "LANG", "LC_ALL", "PATH", "TMPDIR")


@dataclass
class Skill:
    """A reusable workflow that may contain prompt and explicitly approved shell actions."""

    name: str
    description: str
    triggers: list[str] = field(default_factory=list)
    prompt_template: str = ""
    actions: list[dict[str, Any]] = field(default_factory=list)
    requires_approval: bool = True


class SkillRegistry:
    """Manage locally stored skills and execute their shell actions defensively."""

    def __init__(self, skills_dir: str = "skills") -> None:
        self.skills_dir = Path(skills_dir)
        self.skills: dict[str, Skill] = {}
        self._load_skills()

    def _load_skills(self) -> None:
        """Load syntactically valid skill definitions from the configured directory."""
        if not self.skills_dir.exists():
            return
        for skill_file in self.skills_dir.glob("*.json"):
            try:
                data = json.loads(skill_file.read_text(encoding="utf-8"))
                skill = Skill(
                    name=data.get("name", skill_file.stem),
                    description=data.get("description", ""),
                    triggers=data.get("triggers", []),
                    prompt_template=data.get("prompt_template", ""),
                    actions=data.get("actions", []),
                    requires_approval=data.get("requires_approval", True),
                )
                self.skills[skill.name] = skill
            except (OSError, ValueError, TypeError):
                continue

    def register(self, skill: Skill) -> None:
        """Register an in-memory skill definition."""
        self.skills[skill.name] = skill

    def find_skill(self, query: str) -> Skill | None:
        """Find a skill matching a query or one of its triggers."""
        normalized = query.lower()
        for skill in self.skills.values():
            if normalized in skill.name.lower() or normalized in skill.description.lower():
                return skill
            if any(normalized in trigger.lower() for trigger in skill.triggers):
                return skill
        return None

    def list_skills(self) -> list[dict[str, Any]]:
        """List registered skills without exposing their action bodies."""
        return [
            {"name": skill.name, "description": skill.description, "triggers": skill.triggers}
            for skill in self.skills.values()
        ]

    @staticmethod
    def _safe_environment() -> dict[str, str]:
        return {
            key: value
            for key in _SAFE_ENVIRONMENT_KEYS
            if (value := os.environ.get(key))
        }

    @staticmethod
    def _bounded_timeout(value: Any) -> int:
        try:
            requested = int(value)
        except (TypeError, ValueError):
            return SKILL_ACTION_TIMEOUT_SECONDS
        return max(1, min(requested, SKILL_ACTION_TIMEOUT_SECONDS))

    @staticmethod
    def _bounded_output(value: str) -> str:
        if len(value) <= SKILL_ACTION_OUTPUT_MAX_CHARS:
            return value
        return value[:SKILL_ACTION_OUTPUT_MAX_CHARS] + "\n... [truncated]"

    def execute_skill(self, name: str, context: dict[str, Any]) -> dict[str, Any]:
        """Execute a named skill; shell actions require explicit context approval."""
        skill = self.skills.get(name)
        if not skill:
            return {"success": False, "error": f"Skill not found: {name}"}
        has_shell_action = any(action.get("type") == "shell" for action in skill.actions)
        if has_shell_action and skill.requires_approval and context.get("approved") is not True:
            return {"success": False, "error": "Skill shell execution requires explicit approval"}

        results: list[dict[str, Any]] = []
        for action in skill.actions:
            action_type = action.get("type")
            if action_type == "shell":
                command = self._interpolate(str(action.get("command", "")), context)
                try:
                    argv = shlex.split(command)
                    if not argv:
                        raise ValueError("Shell action command cannot be empty")
                    result = subprocess.run(
                        argv,
                        shell=False,
                        capture_output=True,
                        text=True,
                        timeout=self._bounded_timeout(action.get("timeout", SKILL_ACTION_TIMEOUT_SECONDS)),
                        env=self._safe_environment(),
                    )
                    results.append(
                        {
                            "type": "shell",
                            "program": argv[0],
                            "returncode": result.returncode,
                            "output": self._bounded_output(result.stdout),
                            "error": self._bounded_output(result.stderr),
                        }
                    )
                except subprocess.TimeoutExpired:
                    results.append(
                        {
                            "type": "shell",
                            "program": command.split(maxsplit=1)[0] if command.strip() else "",
                            "error": f"Skill action timed out after {self._bounded_timeout(action.get('timeout'))} seconds",
                        }
                    )
                except (OSError, ValueError) as exc:
                    results.append({"type": "shell", "error": f"Skill action failed: {exc}"})
            elif action_type == "prompt":
                results.append(
                    {"type": "prompt", "content": self._interpolate(str(action.get("content", "")), context)}
                )
            else:
                results.append({"type": str(action_type), "error": "Unsupported skill action"})
        return {"success": True, "results": results}

    @staticmethod
    def _interpolate(template: str, context: dict[str, Any]) -> str:
        """Interpolate explicit context values into a skill action template."""
        for key, value in context.items():
            template = template.replace(f"{{{key}}}", str(value))
        return template


def create_skill(name: str, description: str, triggers: list[str], actions: list[dict[str, Any]]) -> Skill:
    """Create a skill definition."""
    return Skill(name=name, description=description, triggers=triggers, actions=actions)


def save_skill(skill: Skill, skills_dir: str = "skills") -> None:
    """Persist a skill definition with owner-only file permissions."""
    directory = Path(skills_dir)
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        directory.chmod(0o700)
    except OSError:
        pass
    skill_file = directory / f"{skill.name}.json"
    payload = json.dumps(
        {
            "name": skill.name,
            "description": skill.description,
            "triggers": skill.triggers,
            "actions": skill.actions,
            "requires_approval": skill.requires_approval,
        },
        indent=2,
    )
    descriptor = os.open(skill_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as skill_handle:
            skill_handle.write(payload)
            skill_handle.flush()
            os.fsync(skill_handle.fileno())
    finally:
        try:
            skill_file.chmod(0o600)
        except OSError:
            pass


_registry: SkillRegistry | None = None


def get_registry() -> SkillRegistry:
    """Return the process-local skill registry singleton."""
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
    return _registry


EXAMPLE_SKILL = {
    "name": "code_review",
    "description": "Automated code review workflow",
    "triggers": ["review", "code review", "check code"],
    "actions": [
        {"type": "shell", "command": "ruff check {file}", "timeout": 30},
        {"type": "shell", "command": "mypy {file}", "timeout": 60},
        {"type": "shell", "command": "git diff --stat {file}", "timeout": 10},
    ],
    "requires_approval": True,
}
