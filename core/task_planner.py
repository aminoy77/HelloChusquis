from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable
from enum import Enum
import asyncio


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskStep:
    id: int
    description: str
    status: TaskStatus = TaskStatus.PENDING
    result: str = ""
    error: str = ""


@dataclass
class Task:
    id: str
    title: str
    description: str
    steps: list[TaskStep] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = ""
    completed_at: str = ""

    def add_step(self, description: str) -> TaskStep:
        step = TaskStep(id=len(self.steps) + 1, description=description)
        self.steps.append(step)
        return step

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "steps": [
                {"id": s.id, "description": s.description, "status": s.status.value, "result": s.result, "error": s.error}
                for s in self.steps
            ],
            "created_at": self.created_at,
            "completed_at": self.completed_at
        }


class TaskPlanner:
    """Plan and execute multi-step tasks with agent support."""

    def __init__(self):
        self.tasks: dict[str, Task] = {}
        self.task_callbacks: dict[str, Callable] = {}

    def create_task(self, title: str, description: str = "") -> Task:
        from datetime import datetime
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        task = Task(
            id=task_id,
            title=title,
            description=description,
            created_at=datetime.now().isoformat()
        )
        self.tasks[task_id] = task
        return task

    def parse_task_from_text(self, text: str) -> Task:
        """Parse a task description into structured steps."""
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        title = lines[0] if lines else "Untitled Task"
        description = "\n".join(lines[1:]) if len(lines) > 1 else ""

        task = self.create_task(title, description)

        for line in lines[1:]:
            if line.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "-", "•", "*")):
                step_text = line.lstrip("123456789.-*• ").strip()
                if step_text:
                    task.add_step(step_text)

        return task

    def execute_step(self, task_id: str, step_id: int, executor: Callable) -> TaskStep:
        """Execute a single step with the given executor function."""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        step = next((s for s in task.steps if s.id == step_id), None)
        if not step:
            raise ValueError(f"Step {step_id} not found")

        step.status = TaskStatus.RUNNING

        try:
            result = executor(step.description)
            step.result = str(result)
            step.status = TaskStatus.COMPLETED
        except Exception as e:
            step.error = str(e)
            step.status = TaskStatus.FAILED

        return step

    async def execute_all_steps(self, task_id: str, executor: Callable, confirm_each: bool = True) -> Task:
        """Execute all steps sequentially with optional confirmation."""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        for step in task.steps:
            if confirm_each:
                confirm = input(f"Execute: {step.description}? [Y/n] ")
                if confirm.lower() == "n":
                    step.status = TaskStatus.CANCELLED
                    continue

            self.execute_step(task_id, step.id, executor)

            if step.status == TaskStatus.FAILED:
                task.status = TaskStatus.FAILED
                break

        task.status = TaskStatus.COMPLETED if all(
            s.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED) for s in task.steps
        ) else TaskStatus.RUNNING

        return task

    def get_task(self, task_id: str) -> Task | None:
        return self.tasks.get(task_id)

    def list_tasks(self, status: TaskStatus | None = None) -> list[Task]:
        tasks = list(self.tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)

    def cancel_task(self, task_id: str):
        task = self.tasks.get(task_id)
        if task:
            task.status = TaskStatus.CANCELLED
            for step in task.steps:
                if step.status == TaskStatus.PENDING:
                    step.status = TaskStatus.CANCELLED

    def generate_plan_prompt(self, user_request: str) -> str:
        """Generate a task plan from a user request."""
        return f"""Based on this request: "{user_request}"

Break it down into clear, executable steps:

1. Identify the main goal
2. List required sub-tasks in order
3. Note any dependencies between tasks
4. Identify potential blockers or questions

Provide the plan as a numbered list that can be executed step by step."""


def get_planner() -> TaskPlanner:
    return TaskPlanner()