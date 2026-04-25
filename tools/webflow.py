from httpx import AsyncClient
import json


async def create_site(name: str, api_key: str, team_id: str = None) -> dict:
    """Create Webflow site."""
    url = "https://api.webflow.com/sites"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name, "teamId": team_id},
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
        return r.json()


async def get_sites(api_key: str) -> dict:
    """Get Webflow sites."""
    url = "https://api.webflow.com/sites"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def create_collection(site_id: str, name: str, slug: str, api_key: str) -> dict:
    """Create collection."""
    url = f"https://api.webflow.com/sites/{site_id}/collections"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name, "slug": slug},
            headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def publish_collection(site_id: str, collection_id: str, api_key: str) -> dict:
    """Publish collection."""
    url = f"https://api.webflow.com/collections/{collection_id}/publish"
    async with AsyncClient() as client:
        r = await client.post(url, json={"siteId": site_id},
            headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def create_item(collection_id: str, fields: dict, api_key: str) -> dict:
    """Create collection item."""
    url = f"https://api.webflow.com/collections/{collection_id}/items"
    async with AsyncClient() as client:
        r = await client.post(url, json={"fields": fields},
            headers={"Authorization": f"Bearer {api_key}"})
        return r.json()