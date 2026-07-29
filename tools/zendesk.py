from httpx import AsyncClient


async def create_ticket(api_key: str, subdomain: str, subject: str, description: str, requester: str, **kwargs) -> dict:
    """Create Zendesk ticket."""
    url = f"https://{subdomain}.zendesk.com/api/v2/tickets.json"
    async with AsyncClient() as client:
        r = await client.post(url, json={
            "ticket": {"subject": subject, "description": description, "requester": {"email": requester}, **kwargs}
        }, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def list_tickets(api_key: str, subdomain: str) -> dict:
    """List Zendesk tickets."""
    url = f"https://{subdomain}.zendesk.com/api/v2/tickets.json"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def update_ticket(api_key: str, subdomain: str, ticket_id: str, **kwargs) -> dict:
    """Update Zendesk ticket."""
    url = f"https://{subdomain}.zendesk.com/api/v2/tickets/{ticket_id}.json"
    async with AsyncClient() as client:
        r = await client.put(url, json={"ticket": kwargs}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def search_tickets(api_key: str, subdomain: str, query: str) -> dict:
    """Search Zendesk tickets."""
    url = f"https://{subdomain}.zendesk.com/api/v2/search.json?query={query}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def add_comment(api_key: str, subdomain: str, ticket_id: str, body: str, author_id: str) -> dict:
    """Add comment to Zendesk ticket."""
    url = f"https://{subdomain}.zendesk.com/api/v2/tickets/{ticket_id}.json"
    async with AsyncClient() as client:
        r = await client.put(url, json={"ticket": {"comment": {"body": body, "author_id": author_id}}}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()