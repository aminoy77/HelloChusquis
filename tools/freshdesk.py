from httpx import AsyncClient


async def create_ticket(account: str, token: str, subject: str, description: str, email: str) -> dict:
    """Create Freshdesk ticket."""
    url = f"https://{account}.freshdesk.com/api/v2/tickets"
    async with AsyncClient() as client:
        r = await client.post(url, json={
            "subject": subject,
            "description": description,
            "email": email,
            "status": 2,
            "priority": 1
        }, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def list_tickets(account: str, token: str, filter: str = "open") -> dict:
    """List Freshdesk tickets."""
    url = f"https://{account}.freshdesk.com/api/v2/tickets?filter_type={filter}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def get_ticket(account: str, token: str, ticket_id: int) -> dict:
    """Get Freshdesk ticket."""
    url = f"https://{account}.freshdesk.com/api/v2/tickets/{ticket_id}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def update_ticket(account: str, token: str, ticket_id: int, **kwargs) -> dict:
    """Update Freshdesk ticket."""
    url = f"https://{account}.freshdesk.com/api/v2/tickets/{ticket_id}"
    async with AsyncClient() as client:
        r = await client.put(url, json=kwargs, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def add_reply(account: str, token: str, ticket_id: int, body: str) -> dict:
    """Add reply to Freshdesk ticket."""
    url = f"https://{account}.freshdesk.com/api/v2/tickets/{ticket_id}/reply"
    async with AsyncClient() as client:
        r = await client.post(url, json={"body": body}, headers={"Authorization": f"Bearer {token}"})
        return r.json()