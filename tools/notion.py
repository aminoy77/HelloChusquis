from typing import Optional
from httpx import AsyncClient
import os
import httpx


async def create_page(token: str, parent_id: str, title: str, content: str, children: Optional[list] = None) -> dict:
    """Create Notion page."""
    if children is None:
        children = []
    url = "https://api.notion.com/v1/pages"
    async with AsyncClient() as client:
        r = await client.post(url, json={
            "parent": {"page_id": parent_id},
            "properties": {"title": {"title": [{"text": {"content": title}}]}},
            "children": children
        }, headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"})
        return r.json()


async def update_page(token: str, page_id: str, properties: dict) -> dict:
    """Update Notion page."""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    async with AsyncClient() as client:
        r = await client.patch(url, json={"properties": properties}, headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"})
        return r.json()


async def get_page(token: str, page_id: str) -> dict:
    """Get Notion page."""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"})
        return r.json()


async def query_database(token: str, database_id: str, filter: dict = None) -> dict:
    """Query Notion database."""
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    async with AsyncClient() as client:
        r = await client.post(url, json={"filter": filter} if filter else {}, headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"})
        return r.json()


async def append_block(token: str, block_id: str, children: list) -> dict:
    """Append block to Notion page."""
    url = f"https://api.notion.com/v1/blocks/{block_id}/children"
    async with AsyncClient() as client:
        r = await client.patch(url, json={"children": children}, headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"})
        return r.json()


def run(action: str, **kwargs) -> str:
    """Synchronous dispatcher for Notion API actions."""
    token = kwargs.get("token") or os.getenv("NOTION_TOKEN")
    if not token:
        return "Error: No Notion token found. Set NOTION_TOKEN environment variable."
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return _run_sync(action, token, kwargs)
        return loop.run_until_complete(_run_async(action, token, kwargs))
    except RuntimeError:
        return _run_sync(action, token, kwargs)


async def _run_async(action: str, token: str, kwargs: dict) -> str:
    """Async dispatcher for Notion operations."""
    if action == "create_page":
        return str(await create_page(token, kwargs.get("parent_id", ""), kwargs.get("title", ""), kwargs.get("content", ""), kwargs.get("children")))
    elif action == "update_page":
        return str(await update_page(token, kwargs.get("page_id", ""), kwargs.get("properties", {})))
    elif action == "get_page":
        return str(await get_page(token, kwargs.get("page_id", "")))
    elif action == "query_database":
        return str(await query_database(token, kwargs.get("database_id", ""), kwargs.get("filter")))
    elif action == "append_block":
        return str(await append_block(token, kwargs.get("block_id", ""), kwargs.get("children", [])))
    else:
        return f"Error: Unknown action '{action}'. Available: create_page, update_page, get_page, query_database, append_block"


def _run_sync(action: str, token: str, kwargs: dict) -> str:
    """Synchronous fallback using httpx.Client."""
    headers = {"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"}
    try:
        client = httpx.Client(timeout=30)
        if action == "create_page":
            r = client.post("https://api.notion.com/v1/pages", json={
                "parent": {"page_id": kwargs.get("parent_id", "")},
                "properties": {"title": {"title": [{"text": {"content": kwargs.get("title", "")}}]}},
                "children": kwargs.get("children", [])
            }, headers=headers)
            return str(r.json())[:2000]
        elif action == "update_page":
            r = client.patch(f"https://api.notion.com/v1/pages/{kwargs.get('page_id', '')}",
                           json={"properties": kwargs.get("properties", {})}, headers=headers)
            return str(r.json())[:2000]
        elif action == "get_page":
            r = client.get(f"https://api.notion.com/v1/pages/{kwargs.get('page_id', '')}", headers=headers)
            return str(r.json())[:2000]
        elif action == "query_database":
            payload = {"filter": kwargs.get("filter")} if kwargs.get("filter") else {}
            r = client.post(f"https://api.notion.com/v1/databases/{kwargs.get('database_id', '')}/query",
                           json=payload, headers=headers)
            return str(r.json())[:2000]
        elif action == "append_block":
            r = client.patch(f"https://api.notion.com/v1/blocks/{kwargs.get('block_id', '')}/children",
                           json={"children": kwargs.get("children", [])}, headers=headers)
            return str(r.json())[:2000]
        else:
            return f"Error: Unknown action '{action}'. Available: create_page, update_page, get_page, query_database, append_block"
    except Exception as e:
        return f"Error: {str(e)}"