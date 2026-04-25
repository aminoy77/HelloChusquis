from httpx import AsyncClient
import json


async def create_workspace(name: str, org_id: str, api_key: str) -> dict:
    """Create ClickUp workspace."""
    url = "https://api.clickup.com/api/v2/team"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name}, headers={"Authorization": api_key})
        return r.json()


async def create_folder(space_id: str, name: str, api_key: str) -> dict:
    """Create ClickUp folder."""
    url = f"https://api.clickup.com/api/v2/space/{space_id}/folder"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name}, headers={"Authorization": api_key})
        return r.json()


async def create_task(list_id: str, name: str, description: str, api_key: str, **kwargs) -> dict:
    """Create ClickUp task."""
    url = f"https://api.clickup.com/api/v2/list/{list_id}/task"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name, "description": description, **kwargs},
            headers={"Authorization": api_key})
        return r.json()


async def get_task(task_id: str, api_key: str) -> dict:
    """Get ClickUp task."""
    url = f"https://api.clickup.com/api/v2/task/{task_id}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": api_key})
        return r.json()


async def update_task(task_id: str, data: dict, api_key: str) -> dict:
    """Update ClickUp task."""
    url = f"https://api.clickup.com/api/v2/task/{task_id}"
    async with AsyncClient() as client:
        r = await client.put(url, json=data, headers={"Authorization": api_key})
        return r.json()


async def set_task_status(task_id: str, status: str, api_key: str) -> dict:
    """Set task status."""
    url = f"https://api.clickup.com/api/v2/task/{task_id}"
    async with AsyncClient() as client:
        r = await client.put(url, json={"status": status}, headers={"Authorization": api_key})
        return r.json()