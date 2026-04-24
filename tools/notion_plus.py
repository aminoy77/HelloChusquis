from httpx import AsyncClient


async def create_space(name: str, api_key: str) -> dict:
    """Create Notion workspace space."""
    url = "https://api.notion.com/v1/users"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def search_pages(api_key: str, query: str) -> dict:
    """Search Notion pages."""
    url = "https://api.notion.com/v1/search"
    async with AsyncClient() as client:
        r = await client.post(url, json={"query": query}, headers={"Authorization": f"Bearer {api_key}", "Notion-Version": "2022-06-28"})
        return r.json()


async def get_block(block_id: str, api_key: str) -> dict:
    """Get Notion block."""
    url = f"https://api.notion.com/v1/blocks/{block_id}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}", "Notion-Version": "2022-06-28"})
        return r.json()


async def archive_page(page_id: str, api_key: str) -> dict:
    """Archive Notion page."""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    async with AsyncClient() as client:
        r = await client.patch(url, json={"archived": True}, headers={"Authorization": f"Bearer {api_key}", "Notion-Version": "2022-06-28"})
        return r.json()


async def list_databases(api_key: str) -> dict:
    """List Notion databases."""
    url = "https://api.notion.com/v1/search"
    async with AsyncClient() as client:
        r = await client.post(url, json={"filter": {"property": "object", "value": "database"}}, headers={"Authorization": f"Bearer {api_key}", "Notion-Version": "2022-06-28"})
        return r.json()