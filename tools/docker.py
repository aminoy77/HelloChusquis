from httpx import AsyncClient


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