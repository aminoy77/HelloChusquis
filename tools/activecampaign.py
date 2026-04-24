from httpx import AsyncClient


async def add_contact(api_key: str, email: str, **properties) -> dict:
    """Add contact to ActiveCampaign."""
    url = "https://api.activecampaign.com/api/3/contact/sync"
    async with AsyncClient() as client:
        r = await client.post(url, json={
            "contact": {"email": email, **properties}
        }, headers={"Api-Key": api_key})
        return r.json()


async def get_contact(api_key: str, email: str) -> dict:
    """Get contact from ActiveCampaign."""
    url = f"https://api.activecampaign.com/api/3/contact/{email}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Api-Key": api_key})
        return r.json()


async def list_contacts(api_key: str, limit: int = 100) -> dict:
    """List contacts from ActiveCampaign."""
    url = f"https://api.activecampaign.com/api/3/contacts?limit={limit}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Api-Key": api_key})
        return r.json()


async def create_deal(api_key: str, name: str, value: float, stage: str = "1") -> dict:
    """Create deal in ActiveCampaign."""
    url = "https://api.activecampaign.com/api/3/deals"
    async with AsyncClient() as client:
        r = await client.post(url, json={"deal": {"name": name, "value": value, "stage": stage}}, headers={"Api-Key": api_key})
        return r.json()


async def update_contact_field(api_key: str, email: str, field: str, value: str) -> dict:
    """Update contact field in ActiveCampaign."""
    url = "https://api.activecampaign.com/api/3/field/sync"
    async with AsyncClient() as client:
        r = await client.post(url, json={"contact": {"email": email, "fieldValues": [{"field": field, "value": value}]}}, headers={"Api-Key": api_key})
        return r.json()