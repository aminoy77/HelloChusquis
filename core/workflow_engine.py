from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import httpx

from tools.shell import ShellTool
from tools.web_fetch import SsrFBlockedError, validate_url_safety


_WORKFLOW_MAX_TIMEOUT_SECONDS = 300
_WORKFLOW_HTTP_METHODS = frozenset({"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"})


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
    """Execute automated workflows without bypassing shared safety controls."""

    def __init__(self, shell_tool: ShellTool | None = None):
        self.workflows: dict[str, Workflow] = {}
        self._registry: dict[str, Callable] = {}
        self._shell_tool = shell_tool

    def _get_shell_tool(self) -> ShellTool:
        if self._shell_tool is None:
            self._shell_tool = ShellTool()
        return self._shell_tool

    @staticmethod
    def _bounded_timeout(value: Any) -> int:
        try:
            timeout = int(value)
        except (TypeError, ValueError):
            return 60
        return max(1, min(timeout, _WORKFLOW_MAX_TIMEOUT_SECONDS))

    def register_action(self, name: str, action: Callable):
        """Register a custom action handler."""
        self._registry[name] = action

    def load_workflow(self, path: str) -> Workflow | None:
        """Load workflow definitions from JSON."""
        try:
            with open(path, encoding="utf-8") as workflow_file:
                data = json.load(workflow_file)
            steps = [WorkflowStep(**step) for step in data.get("steps", [])]
            return Workflow(
                name=data.get("name", "Unnamed"),
                description=data.get("description", ""),
                steps=steps,
                on_success=data.get("on_success", ""),
                on_failure=data.get("on_failure", ""),
            )
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            return None

    def save_workflow(self, workflow: Workflow, path: str):
        """Save workflow to JSON file."""
        data = {
            "name": workflow.name,
            "description": workflow.description,
            "steps": [
                {
                    "name": step.name,
                    "action": step.action,
                    "params": step.params,
                    "retry": step.retry,
                    "timeout": step.timeout,
                }
                for step in workflow.steps
            ],
            "on_success": workflow.on_success,
            "on_failure": workflow.on_failure,
        }
        Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")

    def execute_step(self, step: WorkflowStep, context: dict) -> tuple[bool, str]:
        """Execute a single workflow step through its approved implementation."""
        action = self._registry.get(step.action)
        if action:
            try:
                result = action(**step.params, context=context)
                return True, str(result)
            except Exception:
                return False, "Custom workflow action failed"

        timeout = self._bounded_timeout(step.timeout)
        if step.action == "shell":
            command = step.params.get("command", "")
            if not isinstance(command, str) or not command.strip():
                return False, "Workflow shell step requires a command"
            result = self._get_shell_tool().run(
                action="exec",
                command=command,
                timeout=timeout,
            )
            if result.success:
                return True, result.output
            return False, result.error or "Workflow shell step failed"

        if step.action == "http":
            url = step.params.get("url", "")
            if not isinstance(url, str) or not url.strip():
                return False, "Workflow HTTP step requires a URL"
            try:
                url = validate_url_safety(url.strip())
            except SsrFBlockedError as exc:
                return False, f"SSRF blocked: {exc}"
            except ValueError:
                return False, "Invalid workflow HTTP URL"

            method = str(step.params.get("method", "GET")).upper().strip()
            if method not in _WORKFLOW_HTTP_METHODS:
                return False, "Unsupported workflow HTTP method"
            try:
                response = httpx.request(
                    method=method,
                    url=url,
                    timeout=timeout,
                    follow_redirects=False,
                )
                return response.is_success, response.text[:100_000]
            except httpx.HTTPError:
                return False, "Workflow HTTP request failed"

        if step.action == "wait":
            import time

            duration = self._bounded_timeout(step.params.get("seconds", 1))
            time.sleep(duration)
            return True, f"Waited {duration}s"

        if step.action == "notify":
            from rich.console import Console

            Console().print(f"[bold]Notification:[/bold] {step.params.get('message', '')}")
            return True, "Notified"

        return False, f"Unknown action: {step.action}"

    def execute(self, workflow: Workflow, context: dict | None = None) -> dict:
        """Execute a complete workflow with bounded retries per step."""
        context = context or {}
        results = []
        success = True

        for step in workflow.steps:
            try:
                attempts = max(1, min(int(step.retry), 10))
            except (TypeError, ValueError):
                attempts = 1
            for attempt in range(attempts):
                ok, result = self.execute_step(step, context)
                if ok:
                    results.append({"step": step.name, "status": "success", "result": result})
                    context[step.name] = result
                    break
                if attempt == attempts - 1:
                    results.append({"step": step.name, "status": "failed", "result": result})
                    success = False

        return {"success": success, "results": results, "context": context}


# Example workflow factory
def example_deploy_workflow() -> Workflow:
    return Workflow(
        name="Deploy app",
        description="Install, test, build, and notify",
        steps=[
            WorkflowStep(name="Install deps", action="shell", params={"command": "npm install"}),
            WorkflowStep(name="Run tests", action="shell", params={"command": "npm test"}),
            WorkflowStep(name="Build", action="shell", params={"command": "npm run build"}),
            WorkflowStep(
                name="Notify",
                action="notify",
                params={"message": "Deployment complete!"},
            ),
        ],
    )


_engine: WorkflowEngine | None = None


def get_engine() -> WorkflowEngine:
    global _engine
    if _engine is None:
        _engine = WorkflowEngine()
    return _engine
