from httpx import AsyncClient


async def create_task(name: str, token: str, project_id: str = None) -> dict:
    """Create Asana task."""
    url = "https://app.asana.com/api/1.0/tasks"
    data = {"name": name}
    if project_id:
        data["projects"] = [project_id]
    async with AsyncClient() as client:
        r = await client.post(url, json=data, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def get_tasks(token: str, project_id: str = None) -> dict:
    """Get Asana tasks."""
    url = "https://app.asana.com/api/1.0/tasks"
    params = {}
    if project_id:
        params["project"] = project_id
    async with AsyncClient() as client:
        r = await client.get(url, params=params, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def update_task(token: str, task_id: str, **kwargs) -> dict:
    """Update Asana task."""
    url = f"https://app.asana.com/api/1.0/tasks/{task_id}"
    async with AsyncClient() as client:
        r = await client.put(url, json=kwargs, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def create_subtask(token: str, task_id: str, name: str) -> dict:
    """Create Asana subtask."""
    url = "https://app.asana.com/api/1.0/tasks"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name, "parent": task_id}, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def list_projects(token: str) -> dict:
    """List Asana projects."""
    url = "https://app.asana.com/api/1.0/projects"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        return r.json()