from __future__ import annotations

import json
import os
import asyncio
from dataclasses import dataclass, field
from typing import Callable, Any
from pathlib import Path


@dataclass
class Skill:
    """A reusable skill - bundled workflow that the agent can invoke."""
    name: str
    description: str
    triggers: list[str] = field(default_factory=list)
    prompt_template: str = ""
    actions: list[dict] = field(default_factory=list)
    requires_approval: bool = True
    

class SkillRegistry:
    """Manages agent skills - reusable workflows."""
    
    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = Path(skills_dir)
        self.skills: dict[str, Skill] = {}
        self._load_skills()
    
    def _load_skills(self):
        """Load skills from the skills directory."""
        if not self.skills_dir.exists():
            return
            
        for skill_file in self.skills_dir.glob("*.json"):
            try:
                data = json.loads(skill_file.read_text())
                skill = Skill(
                    name=data.get("name", skill_file.stem),
                    description=data.get("description", ""),
                    triggers=data.get("triggers", []),
                    prompt_template=data.get("prompt_template", ""),
                    actions=data.get("actions", []),
                    requires_approval=data.get("requires_approval", True)
                )
                self.skills[skill.name] = skill
            except Exception:
                pass
    
    def register(self, skill: Skill):
        """Register a new skill."""
        self.skills[skill.name] = skill
    
    def find_skill(self, query: str) -> Skill | None:
        """Find a skill matching the query."""
        query = query.lower()
        for skill in self.skills.values():
            if query in skill.name.lower() or query in skill.description.lower():
                return skill
            for trigger in skill.triggers:
                if query in trigger.lower():
                    return skill
        return None
    
    def list_skills(self) -> list[dict]:
        """List all available skills."""
        return [
            {"name": s.name, "description": s.description, "triggers": s.triggers}
            for s in self.skills.values()
        ]
    
    def execute_skill(self, name: str, context: dict) -> dict:
        """Execute a skill with given context."""
        skill = self.skills.get(name)
        if not skill:
            return {"success": False, "error": f"Skill not found: {name}"}
        
        results = []
        for action in skill.actions:
            action_type = action.get("type")
            if action_type == "shell":
                import subprocess
                cmd = action.get("command", "")
                cmd = self._interpolate(cmd, context)
                try:
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=action.get("timeout", 60))
                    results.append({"type": "shell", "command": cmd, "output": result.stdout, "error": result.stderr})
                except Exception as e:
                    results.append({"type": "shell", "command": cmd, "error": str(e)})
            elif action_type == "prompt":
                results.append({"type": "prompt", "content": self._interpolate(action.get("content", ""), context)})
        
        return {"success": True, "results": results}
    
    def _interpolate(self, template: str, context: dict) -> str:
        """Interpolate template variables from context."""
        for key, value in context.items():
            template = template.replace(f"{{{key}}}", str(value))
        return template


def create_skill(name: str, description: str, triggers: list[str], actions: list[dict]) -> Skill:
    """Create a new skill."""
    return Skill(
        name=name,
        description=description,
        triggers=triggers,
        actions=actions
    )


def save_skill(skill: Skill, skills_dir: str = "skills"):
    """Save a skill to the skills directory."""
    Path(skills_dir).mkdir(exist_ok=True)
    skill_file = Path(skills_dir) / f"{skill.name}.json"
    data = {
        "name": skill.name,
        "description": skill.description,
        "triggers": skill.triggers,
        "actions": skill.actions,
        "requires_approval": skill.requires_approval
    }
    skill_file.write_text(json.dumps(data, indent=2))


_registry = None

def get_registry() -> SkillRegistry:
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
    return _registry


# Example skill: Code Review
EXAMPLE_SKILL = {
    "name": "code_review",
    "description": "Automated code review workflow",
    "triggers": ["review", "code review", "check code"],
    "actions": [
        {"type": "shell", "command": "ruff check {file}", "timeout": 30},
        {"type": "shell", "command": "mypy {file}", "timeout": 60},
        {"type": "shell", "command": "git diff --stat {file}", "timeout": 10}
    ],
    "requires_approval": True
}