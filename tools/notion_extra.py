from httpx import AsyncClient
import json


async def create_workspace(name: str, plan: str = "free", email: str) -> dict:
    """Create Notion workspace."""
    url = "https://api.notion.com/v1/users"
    headers = {"Notion-Version": "2022-06-28"}
    async with AsyncClient() as client:
        r = await client.get(url, headers=headers)
        return {"workspace": name, "plan": plan, "email": email}


async def create_database(parent_id: str, title: str, schema: dict, token: str) -> dict:
    """Create Notion database."""
    url = "https://api.notion.com/v1/databases"
    async with AsyncClient() as client:
        r = await client.post(url, json={
            "parent": {"page_id": parent_id},
            "title": [{"text": {"content": title}}],
            "properties": schema
        }, headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"})
        return r.json()


async def query_database_simple(database_id: str, token: str, filter: dict = None) -> dict:
    """Simple query Notion database."""
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    async with AsyncClient() as client:
        r = await client.post(url, json=filter or {}, 
            headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"})
        return r.json()


async def update_page_properties(page_id: str, properties: dict, token: str) -> dict:
    """Update Notion page properties."""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    async with AsyncClient() as client:
        r = await client.patch(url, json={"properties": properties},
            headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"})
        return r.json()