from httpx import AsyncClient


async def deploy(project: str, branch: str = "main", api_key: str) -> dict:
    """Deploy to Vercel."""
    url = f"https://api.vercel.com/v6/deployments"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": project, "branch": branch}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def get_deployments(project: str, api_key: str, limit: int = 10) -> dict:
    """Get Vercel deployments."""
    url = f"https://api.vercel.com/v6/deployments?project={project}&limit={limit}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def get_deployment(id: str, api_key: str) -> dict:
    """Get Vercel deployment."""
    url = f"https://api.vercel.com/v6/deployments/{id}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def cancel_deployment(id: str, api_key: str) -> dict:
    """Cancel Vercel deployment."""
    url = f"https://api.vercel.com/v6/deployments/{id}/cancel"
    async with AsyncClient() as client:
        r = await client.post(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def get_project(project: str, api_key: str) -> dict:
    """Get Vercel project."""
    url = f"https://api.vercel.com/v6/projects/{project}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()