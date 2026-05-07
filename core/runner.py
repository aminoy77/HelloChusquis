from __future__ import annotations

import asyncio
import os
import signal
import subprocess
import time
from dataclasses import dataclass, field
from typing import Callable, Any
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class BackgroundTask:
    """A background task that runs continuously."""
    name: str
    command: str
    working_dir: str = "."
    environment: dict = field(default_factory=dict)
    restart_on_failure: bool = True
    max_restarts: int = 3
    
    _process: Any = None
    _restarts: int = 0
    _running: bool = False


class BackgroundRunner:
    """Manages background tasks and processes."""
    
    def __init__(self):
        self.tasks: dict[str, BackgroundTask] = {}
        self._running_tasks: set[str] = set()
    
    def register(self, task: BackgroundTask):
        """Register a new background task."""
        self.tasks[task.name] = task
    
    def start(self, name: str) -> dict:
        """Start a background task."""
        task = self.tasks.get(name)
        if not task:
            return {"success": False, "error": f"Task not found: {name}"}
        
        if task._running:
            return {"success": False, "error": "Task already running"}
        
        try:
            env = {**os.environ, **task.environment}
            task._process = subprocess.Popen(
                task.command,
                shell=True,
                cwd=task.working_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            task._running = True
            self._running_tasks.add(name)
            return {"success": True, "pid": task._process.pid, "name": name}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def stop(self, name: str) -> dict:
        """Stop a background task."""
        task = self.tasks.get(name)
        if not task or not task._running:
            return {"success": False, "error": "Task not running"}
        
        try:
            task._process.terminate()
            task._process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            task._process.kill()
        
        task._running = False
        self._running_tasks.discard(name)
        return {"success": True, "name": name}
    
    def restart(self, name: str) -> dict:
        """Restart a background task."""
        task = self.tasks.get(name)
        if not task:
            return {"success": False, "error": f"Task not found: {name}"}
        
        self.stop(name)
        
        if task.restart_on_failure and task._restarts < task.max_restarts:
            task._restarts += 1
            return self.start(name)
        
        return {"success": False, "error": "Max restarts reached"}
    
    def status(self, name: str = None) -> dict:
        """Get status of tasks."""
        if name:
            task = self.tasks.get(name)
            if not task:
                return {"success": False, "error": "Task not found"}
            return {
                "name": task.name,
                "running": task._running,
                "pid": task._process.pid if task._process else None,
                "restarts": task._restarts
            }
        
        return {
            name: {
                "running": task._running,
                "pid": task._process.pid if task._process else None
            }
            for name, task in self.tasks.items()
        }
    
    def list_tasks(self) -> list[dict]:
        """List all registered tasks."""
        return [
            {"name": t.name, "command": t.command, "running": t._running}
            for t in self.tasks.values()
        ]
    
    def logs(self, name: str, lines: int = 50) -> dict:
        """Get recent logs from a task."""
        task = self.tasks.get(name)
        if not task or not task._process:
            return {"success": False, "error": "Task not running"}
        
        import os
        try:
            result = subprocess.run(
                f"ps -p {task._process.pid} -o etime=",
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            return {
                "success": True,
                "pid": task._process.pid,
                "uptime": result.stdout.strip()
            }
        except Exception:
            return {"success": False, "error": "Could not get task info"}


import os

_runner = None

def get_runner() -> BackgroundRunner:
    global _runner
    if _runner is None:
        _runner = BackgroundRunner()
    return _runner