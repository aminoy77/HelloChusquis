from httpx import AsyncClient
import json
import os
import httpx


def run(action: str, **kwargs) -> str:
    """Synchronous dispatcher for ClickUp API actions."""
    api_key = kwargs.get("api_key") or os.getenv("CLICKUP_API_KEY")
    if not api_key:
        return "Error: No ClickUp API key found. Set CLICKUP_API_KEY environment variable."

    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return _run_sync(action, api_key, kwargs)
        return loop.run_until_complete(_run_async(action, api_key, kwargs))
    except RuntimeError:
        return _run_sync(action, api_key, kwargs)


async def _run_async(action: str, api_key: str, kwargs: dict) -> str:
    """Async dispatcher for ClickUp operations."""
    if action == "create_workspace":
        return await create_workspace(kwargs.get("name", ""), kwargs.get("org_id", ""), api_key)
    elif action == "create_folder":
        return await create_folder(kwargs.get("space_id", ""), kwargs.get("name", ""), api_key)
    elif action == "create_task":
        return await create_task(kwargs.get("list_id", ""), kwargs.get("name", ""), kwargs.get("description", ""), api_key, **{k: v for k, v in kwargs.items() if k not in ("api_key", "list_id", "name", "description")})
    elif action == "get_task":
        return await get_task(kwargs.get("task_id", ""), api_key)
    elif action == "update_task":
        return await update_task(kwargs.get("task_id", ""), kwargs.get("data", {}), api_key)
    elif action == "set_task_status":
        return await set_task_status(kwargs.get("task_id", ""), kwargs.get("status", ""), api_key)
    else:
        return f"Error: Unknown action '{action}'. Available: create_workspace, create_folder, create_task, get_task, update_task, set_task_status"


def _run_sync(action: str, api_key: str, kwargs: dict) -> str:
    """Synchronous fallback using httpx.Client."""
    base_url = "https://api.clickup.com/api/v2"
    headers = {"Authorization": api_key}

    try:
        client = httpx.Client(timeout=30)
        if action == "create_workspace":
            r = client.post(f"{base_url}/team", json={"name": kwargs.get("name", "")}, headers=headers)
            return str(r.json())[:2000]
        elif action == "create_folder":
            r = client.post(f"{base_url}/space/{kwargs.get('space_id', '')}/folder", json={"name": kwargs.get("name", "")}, headers=headers)
            return str(r.json())[:2000]
        elif action == "create_task":
            extra = {k: v for k, v in kwargs.items() if k not in ("api_key", "list_id", "name", "description")}
            r = client.post(f"{base_url}/list/{kwargs.get('list_id', '')}/task", json={"name": kwargs.get("name", ""), "description": kwargs.get("description", ""), **extra}, headers=headers)
            return str(r.json())[:2000]
        elif action == "get_task":
            r = client.get(f"{base_url}/task/{kwargs.get('task_id', '')}", headers=headers)
            return str(r.json())[:2000]
        elif action == "update_task":
            r = client.put(f"{base_url}/task/{kwargs.get('task_id', '')}", json=kwargs.get("data", {}), headers=headers)
            return str(r.json())[:2000]
        elif action == "set_task_status":
            r = client.put(f"{base_url}/task/{kwargs.get('task_id', '')}", json={"status": kwargs.get("status", "")}, headers=headers)
            return str(r.json())[:2000]
        else:
            return f"Error: Unknown action '{action}'. Available: create_workspace, create_folder, create_task, get_task, update_task, set_task_status"
    except Exception as e:
        return f"Error: {str(e)}"


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