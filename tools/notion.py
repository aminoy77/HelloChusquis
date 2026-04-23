from httpx import AsyncClient


async def create_page(token: str, parent_id: str, title: str, content: str, children: list = []) -> dict:
    """Create Notion page."""
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