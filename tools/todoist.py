"""Safe Todoist REST helpers."""

from __future__ import annotations

from httpx import AsyncClient

_BASE_URL = "https://api.todoist.com/rest/v2"


async def _request(method: str, path: str, token: str, **kwargs) -> object:
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.request(method, f"{_BASE_URL}{path}", headers={"Authorization": f"Bearer {token}"}, **kwargs)
        response.raise_for_status()
        return response


async def create_task(title: str, token: str, list_id: str | None = None) -> dict:
    """Create a Todoist task."""
    data = {"content": title}
    if list_id:
        data["project_id"] = list_id
    response = await _request("POST", "/tasks", token, json=data)
    return response.json()


async def list_tasks(token: str, project_id: str | None = None) -> dict:
    """List tasks with a safely encoded optional project filter."""
    params = {"project_id": project_id} if project_id else {}
    response = await _request("GET", "/tasks", token, params=params)
    return response.json()


async def complete_task(task_id: int, token: str) -> dict:
    """Complete a task."""
    await _request("POST", f"/tasks/{int(task_id)}/close", token)
    return {"status": "completed"}


async def delete_task(task_id: int, token: str) -> dict:
    """Delete a task."""
    await _request("DELETE", f"/tasks/{int(task_id)}", token)
    return {"status": "deleted"}


async def get_comments(task_id: int, token: str) -> dict:
    """Get task comments with a structured filter."""
    response = await _request("GET", "/comments", token, params={"task_id": int(task_id)})
    return response.json()
