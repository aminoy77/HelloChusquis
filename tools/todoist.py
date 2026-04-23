from httpx import AsyncClient


async def create_task(title: str, token: str, list_id: str = None) -> dict:
    """Create Todoist task."""
    url = "https://api.todoist.com/rest/v2/tasks"
    data = {"content": title}
    if list_id:
        data["project_id"] = list_id
    async with AsyncClient() as client:
        r = await client.post(url, json=data, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def list_tasks(token: str, project_id: str = None) -> dict:
    """List Todoist tasks."""
    url = f"https://api.todoist.com/rest/v2/tasks?project_id={project_id}" if project_id else "https://api.todoist.com/rest/v2/tasks"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def complete_task(task_id: int, token: str) -> dict:
    """Complete Todoist task."""
    url = f"https://api.todoist.com/rest/v2/tasks/{task_id}/close"
    async with AsyncClient() as client:
        r = await client.post(url, headers={"Authorization": f"Bearer {token}"})
        return {"status": "completed"}


async def delete_task(task_id: int, token: str) -> dict:
    """Delete Todoist task."""
    url = f"https://api.todoist.com/rest/v2/tasks/{task_id}"
    async with AsyncClient() as client:
        r = await client.delete(url, headers={"Authorization": f"Bearer {token}"})
        return {"status": "deleted"}


async def get_comments(task_id: int, token: str) -> dict:
    """Get Todoist comments."""
    url = f"https://api.todoist.com/rest/v2/comments?task_id={task_id}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        return r.json()