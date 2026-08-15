from httpx import AsyncClient
import os
import httpx


def run(action: str, **kwargs) -> str:
    """Synchronous dispatcher for Sanity API actions."""
    api_key = kwargs.get("api_key") or os.getenv("SANITY_API_TOKEN")
    if not api_key:
        return "Error: No Sanity API key found. Set SANITY_API_TOKEN environment variable."

    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return _run_sync(action, api_key, kwargs)
        return loop.run_until_complete(_run_async(action, api_key, kwargs))
    except RuntimeError:
        return _run_sync(action, api_key, kwargs)


async def _run_async(action: str, api_key: str, kwargs: dict) -> str:
    """Async dispatcher for Sanity operations."""
    if action == "create_workspace":
        return str(await create_workspace(kwargs.get("name", ""), api_key))[:2000]
    elif action == "create_document":
        return str(await create_document(kwargs.get("project_id", ""), kwargs.get("dataset", ""), kwargs.get("doc_id", ""), kwargs.get("doc", {}), api_key))[:2000]
    elif action == "query":
        return str(await query(kwargs.get("project_id", ""), kwargs.get("dataset", ""), kwargs.get("query", ""), api_key))[:2000]
    elif action == "delete_document":
        return str(await delete_document(kwargs.get("project_id", ""), kwargs.get("dataset", ""), kwargs.get("doc_id", ""), api_key))[:2000]
    else:
        return f"Error: Unknown action '{action}'. Available: create_workspace, create_document, query, delete_document"


def _run_sync(action: str, api_key: str, kwargs: dict) -> str:
    """Synchronous fallback using httpx.Client."""
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        client = httpx.Client(timeout=30)
        if action == "create_workspace":
            r = client.post("https://api.sanity.io/v2021-10-04/projects",
                           json={"name": kwargs.get("name", "")}, headers=headers)
            return str(r.json())[:2000]
        elif action == "create_document":
            project_id = kwargs.get("project_id", "")
            dataset = kwargs.get("dataset", "")
            r = client.post(f"https://{project_id}.api.sanity.io/v2021-10-04/data/mutate/{dataset}",
                           json={"mutations": [{"createOrReplace": {"_id": kwargs.get("doc_id", ""), **kwargs.get("doc", {})}}]},
                           headers=headers)
            return str(r.json())[:2000]
        elif action == "query":
            project_id = kwargs.get("project_id", "")
            dataset = kwargs.get("dataset", "")
            r = client.get(f"https://{project_id}.api.sanity.io/v2021-10-04/data/query/{dataset}",
                          params={"query": kwargs.get("query", "")}, headers=headers)
            return str(r.json())[:2000]
        elif action == "delete_document":
            project_id = kwargs.get("project_id", "")
            dataset = kwargs.get("dataset", "")
            r = client.post(f"https://{project_id}.api.sanity.io/v2021-10-04/data/mutate/{dataset}",
                           json={"mutations": [{"delete": {"id": kwargs.get("doc_id", "")}}]},
                           headers=headers)
            return str(r.json())[:2000]
        else:
            return f"Error: Unknown action '{action}'. Available: create_workspace, create_document, query, delete_document"
    except Exception as e:
        return f"Error: {str(e)}"


async def create_workspace(name: str, api_key: str) -> dict:
    """Create Sanity project."""
    url = "https://api.sanity.io/v2021-10-04/projects"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def create_document(project_id: str, dataset: str, doc_id: str, doc: dict, token: str) -> dict:
    """Create Sanity document."""
    url = f"https://{project_id}.api.sanity.io/v2021-10-04/data/mutate/{dataset}"
    async with AsyncClient() as client:
        r = await client.post(url, json={"mutations": [{"createOrReplace": {"_id": doc_id, **doc}}]},
            headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def query(project_id: str, dataset: str, query: str, token: str) -> dict:
    """Query Sanity."""
    url = f"https://{project_id}.api.sanity.io/v2021-10-04/data/query/{dataset}"
    async with AsyncClient() as client:
        r = await client.get(url, params={"query": query}, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def delete_document(project_id: str, dataset: str, doc_id: str, token: str) -> dict:
    """Delete Sanity document."""
    url = f"https://{project_id}.api.sanity.io/v2021-10-04/data/mutate/{dataset}"
    async with AsyncClient() as client:
        r = await client.post(url, json={"mutations": [{"delete": {"id": doc_id}}]},
            headers={"Authorization": f"Bearer {token}"})
        return r.json()