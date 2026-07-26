# DEPRECATED: This module is not used. Consider removing.
from __future__ import annotations
import json
import subprocess
from dataclasses import dataclass
from typing import Callable
from pathlib import Path


@dataclass
class WorkflowStep:
    name: str
    action: str
    params: dict
    retry: int = 3
    timeout: int = 60


@dataclass
class Workflow:
    name: str
    description: str
    steps: list[WorkflowStep]
    on_success: str = ""
    on_failure: str = ""


class WorkflowEngine:
    """Execute automated workflows from JSON definitions."""

    def __init__(self):
        self.workflows: dict[str, Workflow] = {}
        self._registry: dict[str, Callable] = {}

    def register_action(self, name: str, action: Callable):
        """Register a custom action handler."""
        self._registry[name] = action

    def load_workflow(self, path: str) -> Workflow | None:
        """Load workflow from JSON file."""
        try:
            with open(path) as f:
                data = json.load(f)
            steps = [WorkflowStep(**s) for s in data.get("steps", [])]
            return Workflow(
                name=data.get("name", "Unnamed"),
                description=data.get("description", ""),
                steps=steps,
                on_success=data.get("on_success", ""),
                on_failure=data.get("on_failure", "")
            )
        except Exception:
            return None

    def save_workflow(self, workflow: Workflow, path: str):
        """Save workflow to JSON file."""
        data = {
            "name": workflow.name,
            "description": workflow.description,
            "steps": [
                {"name": s.name, "action": s.action, "params": s.params, "retry": s.retry, "timeout": s.timeout}
                for s in workflow.steps
            ],
            "on_success": workflow.on_success,
            "on_failure": workflow.on_failure
        }
        Path(path).write_text(json.dumps(data, indent=2))

    def execute_step(self, step: WorkflowStep, context: dict) -> tuple[bool, str]:
        """Execute a single workflow step."""
        action = self._registry.get(step.action)

        if action:
            try:
                result = action(**step.params, context=context)
                return True, str(result)
            except Exception as e:
                return False, str(e)

        if step.action == "shell":
            try:
                cmd = step.params.get("command", "")
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=step.timeout)
                return result.returncode == 0, result.stdout + result.stderr
            except Exception as e:
                return False, str(e)

        if step.action == "http":
            import httpx
            try:
                r = httpx.request(
                    method=step.params.get("method", "GET"),
                    url=step.params.get("url", ""),
                    timeout=step.timeout
                )
                return r.is_success, r.text
            except Exception as e:
                return False, str(e)

        if step.action == "wait":
            import time
            duration = step.params.get("seconds", 1)
            time.sleep(duration)
            return True, f"Waited {duration}s"

        if step.action == "notify":
            from rich.console import Console
            Console().print(f"[bold]Notification:[/bold] {step.params.get('message', '')}")
            return True, "Notified"

        return False, f"Unknown action: {step.action}"

    def execute(self, workflow: Workflow, context: dict = None) -> dict:
        """Execute a complete workflow."""
        context = context or {}
        results = []
        success = True

        for step in workflow.steps:
            for attempt in range(step.retry):
                ok, result = self.execute_step(step, context)
                if ok:
                    results.append({"step": step.name, "status": "success", "result": result})
                    context[step.name] = result
                    break
                if attempt == step.retry - 1:
                    results.append({"step": step.name, "status": "failed", "error": result})
                    success = False
                    if workflow.on_failure:
                        self._execute_hook(workflow.on_failure, context)
                    return {"success": False, "results": results, "context": context}

        if success and workflow.on_success:
            self._execute_hook(workflow.on_success, context)

        return {"success": success, "results": results, "context": context}

    def _execute_hook(self, hook: str, context: dict):
        """Execute a hook (on_success or on_failure)."""
        pass

    def create_example_workflow(self, name: str) -> Workflow:
        """Create an example deployment workflow."""
        return Workflow(
            name=name,
            description="Example deployment workflow",
            steps=[
                WorkflowStep(name="Install deps", action="shell", params={"command": "npm install"}),
                WorkflowStep(name="Run tests", action="shell", params={"command": "npm test"}),
                WorkflowStep(name="Build", action="shell", params={"command": "npm run build"}),
                WorkflowStep(name="Notify", action="notify", params={"message": "Deployment complete!"})
            ],
            on_success="notify_success",
            on_failure="notify_failure"
        )


def get_engine() -> WorkflowEngine:
    return WorkflowEngine()