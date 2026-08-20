"""Safe lifecycle management for explicitly registered background tasks."""

from __future__ import annotations

import os
from pathlib import Path
import shlex
import signal
import subprocess
from dataclasses import dataclass, field
from typing import Any


BACKGROUND_STOP_TIMEOUT_SECONDS = 5
_SAFE_ENVIRONMENT_KEYS = ("HOME", "LANG", "LC_ALL", "PATH", "TMPDIR")


@dataclass
class BackgroundTask:
    """An explicitly registered process that may run after the current request."""

    name: str
    command: str
    working_dir: str = "."
    environment: dict[str, str] = field(default_factory=dict)
    restart_on_failure: bool = True
    max_restarts: int = 3
    _process: Any = None
    _restarts: int = 0
    _running: bool = False


class BackgroundRunner:
    """Manage registered background processes without inheriting host secrets."""

    def __init__(self) -> None:
        self.tasks: dict[str, BackgroundTask] = {}
        self._running_tasks: set[str] = set()

    def register(self, task: BackgroundTask) -> None:
        """Register a task definition; process launch still requires start()."""
        self.tasks[task.name] = task

    @staticmethod
    def _environment(task: BackgroundTask) -> dict[str, str]:
        environment = {
            key: value
            for key in _SAFE_ENVIRONMENT_KEYS
            if (value := os.environ.get(key))
        }
        environment.update({str(key): str(value) for key, value in task.environment.items()})
        return environment

    @staticmethod
    def _command(command: str) -> list[str]:
        parsed = shlex.split(command)
        if not parsed:
            raise ValueError("Task command cannot be empty")
        return parsed

    @staticmethod
    def _working_directory(working_dir: str) -> str:
        resolved = Path(working_dir).expanduser().resolve(strict=True)
        if not resolved.is_dir():
            raise ValueError("Task working directory must be a directory")
        return str(resolved)

    def _mark_finished(self, task: BackgroundTask) -> bool:
        process = task._process
        if not task._running or process is None or process.poll() is None:
            return False
        task._running = False
        task._process = None
        self._running_tasks.discard(task.name)
        return True

    def start(self, name: str) -> dict[str, object]:
        """Start one registered task with no shell, inherited secrets, or open pipes."""
        task = self.tasks.get(name)
        if not task:
            return {"success": False, "error": f"Task not found: {name}"}
        self._mark_finished(task)
        if task._running:
            return {"success": False, "error": "Task already running"}

        try:
            task._process = subprocess.Popen(
                self._command(task.command),
                shell=False,
                cwd=self._working_directory(task.working_dir),
                env=self._environment(task),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
                start_new_session=True,
            )
        except (OSError, ValueError) as exc:
            return {"success": False, "error": f"Could not start task: {exc}"}

        task._running = True
        self._running_tasks.add(name)
        return {"success": True, "pid": task._process.pid, "name": name}

    def stop(self, name: str) -> dict[str, object]:
        """Stop a task and, where supported, its isolated process group."""
        task = self.tasks.get(name)
        if not task:
            return {"success": False, "error": "Task not running"}
        self._mark_finished(task)
        if not task._running or not task._process:
            return {"success": False, "error": "Task not running"}

        process = task._process
        try:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGTERM)
            else:
                process.terminate()
            process.wait(timeout=BACKGROUND_STOP_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
            process.wait(timeout=BACKGROUND_STOP_TIMEOUT_SECONDS)
        except (OSError, ProcessLookupError):
            pass
        finally:
            task._running = False
            task._process = None
            self._running_tasks.discard(name)
        return {"success": True, "name": name}

    def restart(self, name: str) -> dict[str, object]:
        """Restart a failed task up to its declared restart budget."""
        task = self.tasks.get(name)
        if not task:
            return {"success": False, "error": f"Task not found: {name}"}
        self.stop(name)
        if task.restart_on_failure and task._restarts < task.max_restarts:
            task._restarts += 1
            return self.start(name)
        return {"success": False, "error": "Max restarts reached"}

    def status(self, name: str | None = None) -> dict[str, object]:
        """Return current process state, reconciling tasks that have exited."""
        if name:
            task = self.tasks.get(name)
            if not task:
                return {"success": False, "error": "Task not found"}
            self._mark_finished(task)
            return {
                "name": task.name,
                "running": task._running,
                "pid": task._process.pid if task._process else None,
                "restarts": task._restarts,
            }
        for task in self.tasks.values():
            self._mark_finished(task)
        return {
            task_name: {"running": task._running, "pid": task._process.pid if task._process else None}
            for task_name, task in self.tasks.items()
        }

    def list_tasks(self) -> list[dict[str, object]]:
        """List task definitions without exposing environment values."""
        for task in self.tasks.values():
            self._mark_finished(task)
        return [{"name": task.name, "command": task.command, "running": task._running} for task in self.tasks.values()]

    def logs(self, name: str, lines: int = 50) -> dict[str, object]:
        """Return bounded process metadata; output is intentionally not retained."""
        del lines
        task = self.tasks.get(name)
        if not task:
            return {"success": False, "error": "Task not running"}
        self._mark_finished(task)
        if not task._process:
            return {"success": False, "error": "Task not running"}
        try:
            result = subprocess.run(
                ["ps", "-p", str(task._process.pid), "-o", "etime="],
                capture_output=True,
                text=True,
                timeout=BACKGROUND_STOP_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.TimeoutExpired):
            return {"success": False, "error": "Could not get task info"}
        return {"success": True, "pid": task._process.pid, "uptime": result.stdout.strip()[:100]}


_runner: BackgroundRunner | None = None


def get_runner() -> BackgroundRunner:
    """Return the process-local background runner singleton."""
    global _runner
    if _runner is None:
        _runner = BackgroundRunner()
    return _runner
