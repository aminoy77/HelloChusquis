from httpx import AsyncClient


async def subscribe(api_key: str, email: str, **kwargs) -> dict:
    """Add subscriber to ConvertKit."""
    url = "https://api.convertkit.com/v3/forms"
    async with AsyncClient() as client:
        r = await client.post(url, json={"api_key": api_key, "email": email, **kwargs})
        return r.json()


async def get_forms(api_key: str) -> dict:
    """Get ConvertKit forms."""
    url = f"https://api.convertkit.com/v3/forms?api_key={api_key}"
    async with AsyncClient() as client:
        r = await client.get(url)
        return r.json()


async def get_subscribers(api_key: str, page: int = 1) -> dict:
    """Get ConvertKit subscribers."""
    url = f"https://api.convertkit.com/v3/subscribers?api_key={api_key}&page={page}"
    async with AsyncClient() as client:
        r = await client.get(url)
        return r.json()


async def add_to_sequence(api_key: str, sequence_id: str, email: str) -> dict:
    """Add subscriber to sequence."""
    url = f"https://api.convertkit.com/v3/sequences/{sequence_id}/subscribe"
    async with AsyncClient() as client:
        r = await client.post(url, json={"api_key": api_key, "email": email})
        return r.json()


async def create_broadcast(api_key: str, subject: str, content: str) -> dict:
    """Create broadcast in ConvertKit."""
    url = "https://api.convertkit.com/v3/broadcasts"
    async with AsyncClient() as client:
        r = await client.post(url, json={"api_key": api_key, "subject": subject, "content": content})
        return r.json()