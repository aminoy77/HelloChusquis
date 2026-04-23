from httpx import AsyncClient


async def create_lead(email: str, first_name: str, last_name: str, api_key: str) -> dict:
    """Create HubSpot lead."""
    url = "https://api.hubapi.com/crm/v3/objects/contacts"
    async with AsyncClient() as client:
        r = await client.post(url, json={"properties": {"email": email, "firstname": first_name, "lastname": last_name}}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def get_lead(email: str, api_key: str) -> dict:
    """Get HubSpot contact."""
    url = f"https://api.hubapi.com/crm/v3/objects/contacts/{email}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def create_deal(name: str, amount: str, stage: str, api_key: str) -> dict:
    """Create HubSpot deal."""
    url = "https://api.hubapi.com/crm/v3/objects/deals"
    async with AsyncClient() as client:
        r = await client.post(url, json={"properties": {"dealname": name, "amount": amount, "dealstage": stage}}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def create_company(domain: str, name: str, api_key: str) -> dict:
    """Create HubSpot company."""
    url = "https://api.hubapi.com/crm/v3/objects/companies"
    async with AsyncClient() as client:
        r = await client.post(url, json={"properties": {"domain": domain, "name": name}}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()