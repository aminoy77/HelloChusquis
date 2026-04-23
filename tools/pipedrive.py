from httpx import AsyncClient


async def create_company(name: str, api_key: str, **kwargs) -> dict:
    """Create Pipedrive company."""
    url = "https://api.pipedrive.com/v1/companies"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name, **kwargs}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def get_deals(api_key: str, status: str = "open") -> dict:
    """Get Pipedrive deals."""
    url = f"https://api.pipedrive.com/v1/deals?status={status}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def add_activity(api_key: str, subject: str, type: str, due_date: str) -> dict:
    """Add Pipedrive activity."""
    url = "https://api.pipedrive.com/v1/activities"
    async with AsyncClient() as client:
        r = await client.post(url, json={"subject": subject, "type": type, "due_date": due_date}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()