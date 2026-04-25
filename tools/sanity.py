from httpx import AsyncClient


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