from httpx import AsyncClient
import os
import httpx


async def list_containers(api_key: str) -> dict:
    """List Docker containers."""
    url = "http://localhost:2375/containers/json"
    async with AsyncClient() as client:
        r = await client.get(url)
        return r.json()


async def create_container(image: str, name: str, api_key: str) -> dict:
    """Create Docker container."""
    url = "http://localhost:2375/containers/create"
    async with AsyncClient() as client:
        r = await client.post(url, json={"Image": image, "name": name})
        return r.json()


async def start_container(container_id: str, api_key: str) -> dict:
    """Start Docker container."""
    url = f"http://localhost:2375/containers/{container_id}/start"
    async with AsyncClient() as client:
        r = await client.post(url)
        return r.json()


async def stop_container(container_id: str, api_key: str) -> dict:
    """Stop Docker container."""
    url = f"http://localhost:2375/containers/{container_id}/stop"
    async with AsyncClient() as client:
        r = await client.post(url)
        return r.json()


async def remove_container(container_id: str, api_key: str) -> dict:
    """Remove Docker container."""
    url = f"http://localhost:2375/containers/{container_id}"
    async with AsyncClient() as client:
        r = await client.delete(url)
        return {"removed": container_id}


def run(action: str, **kwargs) -> str:
    """Synchronous dispatcher for Docker API actions."""
    api_key = kwargs.get("api_key", "")
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return _run_sync(action, api_key, kwargs)
        return loop.run_until_complete(_run_async(action, api_key, kwargs))
    except RuntimeError:
        return _run_sync(action, api_key, kwargs)


async def _run_async(action: str, api_key: str, kwargs: dict) -> str:
    """Async dispatcher for Docker operations."""
    if action == "list_containers":
        return str(await list_containers(api_key))
    elif action == "create_container":
        return str(await create_container(kwargs.get("image", ""), kwargs.get("name", ""), api_key))
    elif action == "start_container":
        return str(await start_container(kwargs.get("container_id", ""), api_key))
    elif action == "stop_container":
        return str(await stop_container(kwargs.get("container_id", ""), api_key))
    elif action == "remove_container":
        return str(await remove_container(kwargs.get("container_id", ""), api_key))
    else:
        return f"Error: Unknown action '{action}'. Available: list_containers, create_container, start_container, stop_container, remove_container"


def _run_sync(action: str, api_key: str, kwargs: dict) -> str:
    """Synchronous fallback using httpx.Client."""
    try:
        client = httpx.Client(timeout=30)
        if action == "list_containers":
            r = client.get("http://localhost:2375/containers/json")
            return str(r.json())[:2000]
        elif action == "create_container":
            r = client.post("http://localhost:2375/containers/create",
                           json={"Image": kwargs.get("image", ""), "name": kwargs.get("name", "")})
            return str(r.json())[:2000]
        elif action == "start_container":
            cid = kwargs.get("container_id", "")
            r = client.post(f"http://localhost:2375/containers/{cid}/start")
            return str(r.json())[:2000]
        elif action == "stop_container":
            cid = kwargs.get("container_id", "")
            r = client.post(f"http://localhost:2375/containers/{cid}/stop")
            return str(r.json())[:2000]
        elif action == "remove_container":
            cid = kwargs.get("container_id", "")
            r = client.delete(f"http://localhost:2375/containers/{cid}")
            return str({"removed": cid})
        else:
            return f"Error: Unknown action '{action}'. Available: list_containers, create_container, start_container, stop_container, remove_container"
    except Exception as e:
        return f"Error: {str(e)}"