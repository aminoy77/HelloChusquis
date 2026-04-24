from httpx import AsyncClient


async def create_workspace(name: str, api_key: str) -> dict:
    """Create Airtable workspace."""
    url = "https://api.airtable.com/v0/meta/workspaces"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def list_bases(api_key: str) -> dict:
    """List Airtable bases."""
    url = "https://api.airtable.com/v0/meta/bases"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def create_base(api_key: str, name: str, workspace_id: str) -> dict:
    """Create Airtable base."""
    url = "https://api.airtable.com/v0/meta/bases"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name, "workspaceId": workspace_id}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def list_tables(base_id: str, api_key: str) -> dict:
    """List Airtable tables."""
    url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def create_field(base_id: str, table_id: str, field_name: str, field_type: str, api_key: str) -> dict:
    """Create Airtable field."""
    url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables/{table_id}"
    async with AsyncClient() as client:
        r = await client.post(url, json={"fields": [{"name": field_name, "type": field_type}]}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()