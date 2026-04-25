from httpx import AsyncClient
import json


async def create_workspace(org_name: str, api_key: str) -> dict:
    """Create Airtable base."""
    url = "https://api.airtable.com/v0/meta/bases"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": org_name},
            headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def create_table(base_id: str, table_name: str, fields: list, api_key: str) -> dict:
    """Create Airtable table."""
    url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": table_name, "fields": fields},
            headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def create_record(table_id: str, record: dict, api_key: str) -> dict:
    """Create Airtable record."""
    url = f"https://api.airtable.com/v0/{table_id}"
    async with AsyncClient() as client:
        r = await client.post(url, json={"fields": record},
            headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def update_record(table_id: str, record_id: str, record: dict, api_key: str) -> dict:
    """Update Airtable record."""
    url = f"https://api.airtable.com/v0/{table_id}/{record_id}"
    async with AsyncClient() as client:
        r = await client.patch(url, json={"fields": record},
            headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def delete_record(table_id: str, record_id: str, api_key: str) -> dict:
    """Delete Airtable record."""
    url = f"https://api.airtable.com/v0/{table_id}/{record_id}"
    async with AsyncClient() as client:
        r = await client.delete(url, headers={"Authorization": f"Bearer {api_key}"})
        return {"deleted": record_id}