from httpx import AsyncClient
import os
import httpx


def run(action: str, **kwargs) -> str:
    """Synchronous dispatcher for Vercel API actions."""
    api_key = kwargs.get("api_key") or os.getenv("VERCEL_API_KEY")
    if not api_key:
        return "Error: No Vercel API key found. Set VERCEL_API_KEY environment variable."

    import asyncio
    try:
        loop = asyncio.get_running_loop()
        import concurrent.futures
        fut = asyncio.run_coroutine_threadsafe(_run_async(action, api_key, kwargs), loop)
        return fut.result(timeout=30)
    except RuntimeError:
        return _run_sync(action, api_key, kwargs)


async def _run_async(action: str, api_key: str, kwargs: dict) -> str:
    """Async dispatcher for Vercel operations."""
    if action == "deploy":
        return str(await deploy(api_key, kwargs.get("project", ""), kwargs.get("branch", "main")))[2000]
    elif action == "get_deployments":
        return str(await get_deployments(kwargs.get("project", ""), api_key, kwargs.get("limit", 10)))[2000]
    elif action == "get_deployment":
        return str(await get_deployment(kwargs.get("id", ""), api_key))[:2000]
    elif action == "cancel_deployment":
        return str(await cancel_deployment(kwargs.get("id", ""), api_key))[:2000]
    elif action == "get_project":
        return str(await get_project(kwargs.get("project", ""), api_key))[:2000]
    else:
        return f"Error: Unknown action '{action}'. Available: deploy, get_deployments, get_deployment, cancel_deployment, get_project"


def _run_sync(action: str, api_key: str, kwargs: dict) -> str:
    """Synchronous fallback using httpx.Client."""
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        client = httpx.Client(timeout=30)
        if action == "deploy":
            r = client.post("https://api.vercel.com/v6/deployments",
                           json={"name": kwargs.get("project", ""), "branch": kwargs.get("branch", "main")},
                           headers=headers)
            return str(r.json())[:2000]
        elif action == "get_deployments":
            project = kwargs.get("project", "")
            limit = kwargs.get("limit", 10)
            r = client.get(f"https://api.vercel.com/v6/deployments?project={project}&limit={limit}", headers=headers)
            return str(r.json())[:2000]
        elif action == "get_deployment":
            r = client.get(f"https://api.vercel.com/v6/deployments/{kwargs.get('id', '')}", headers=headers)
            return str(r.json())[:2000]
        elif action == "cancel_deployment":
            r = client.post(f"https://api.vercel.com/v6/deployments/{kwargs.get('id', '')}/cancel", headers=headers)
            return str(r.json())[:2000]
        elif action == "get_project":
            r = client.get(f"https://api.vercel.com/v6/projects/{kwargs.get('project', '')}", headers=headers)
            return str(r.json())[:2000]
        else:
            return f"Error: Unknown action '{action}'. Available: deploy, get_deployments, get_deployment, cancel_deployment, get_project"
    except Exception as e:
        return f"Error: {str(e)}"


async def deploy(api_key: str, project: str, branch: str = "main") -> dict:
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