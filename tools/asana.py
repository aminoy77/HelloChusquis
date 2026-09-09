"""Bounded Asana API helpers."""

from __future__ import annotations

import re

from httpx import AsyncClient

_TASK_ID_RE = re.compile(r"^[0-9]{1,32}$")


def _task_id(value: object) -> str:
    task_id = str(value or "")
    if not _TASK_ID_RE.fullmatch(task_id):
        raise ValueError("Invalid Asana task ID.")
    return task_id


async def create_task(name: str, token: str, project_id: str | None = None) -> dict:
    """Create an Asana task."""
    data = {"name": name}
    if project_id:
        data["projects"] = [project_id]
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.post("https://app.asana.com/api/1.0/tasks", json=data, headers={"Authorization": f"Bearer {token}"})
        response.raise_for_status()
        return response.json()


async def get_tasks(token: str, project_id: str | None = None) -> dict:
    """List tasks, optionally for a project."""
    params = {"project": project_id} if project_id else {}
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.get("https://app.asana.com/api/1.0/tasks", params=params, headers={"Authorization": f"Bearer {token}"})
        response.raise_for_status()
        return response.json()


async def update_task(token: str, task_id: str, **kwargs) -> dict:
    """Update a task using a validated task identifier."""
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.put(
            f"https://app.asana.com/api/1.0/tasks/{_task_id(task_id)}",
            json=kwargs,
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        return response.json()


async def create_subtask(token: str, task_id: str, name: str) -> dict:
    """Create an Asana subtask."""
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.post(
            "https://app.asana.com/api/1.0/tasks",
            json={"name": name, "parent": _task_id(task_id)},
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        return response.json()


async def list_projects(token: str) -> dict:
    """List Asana projects."""
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.get("https://app.asana.com/api/1.0/projects", headers={"Authorization": f"Bearer {token}"})
        response.raise_for_status()
        return response.json()
