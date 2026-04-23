from httpx import AsyncClient


async def create_ticket(email: str, subject: str, body: str, auth: str) -> dict:
    """Create HelpScout ticket."""
    url = "https://api.helpscout.net/v2/conversations"
    async with AsyncClient() as client:
        r = await client.post(url, json={
            "customer": {"email": email},
            "subject": subject,
            "mailbox": {"id": 1},
            "threads": [{"type": "customer", "body": body}]
        }, headers={"Authorization": auth, "Content-Type": "application/json"})
        return r.json()


async def list_conversations(auth: str, mailbox: int = 1) -> dict:
    """List HelpScout conversations."""
    url = f"https://api.helpscout.net/v2/mailboxes/{mailbox}/conversations"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": auth})
        return r.json()


async def get_conversation(auth: str, conversation_id: int) -> dict:
    """Get HelpScout conversation."""
    url = f"https://api.helpscout.net/v2/conversations/{conversation_id}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": auth})
        return r.json()


async def add_thread(auth: str, conversation_id: int, body: str, type: str = "customer") -> dict:
    """Add thread to HelpScout conversation."""
    url = f"https://api.helpscout.net/v2/conversations/{conversation_id}/threads"
    async with AsyncClient() as client:
        r = await client.post(url, json={"type": type, "body": body}, headers={"Authorization": auth})
        return r.json()


async def update_ticket_status(auth: str, conversation_id: int, status: str) -> dict:
    """Update HelpScout conversation status."""
    url = f"https://api.helpscout.net/v2/conversations/{conversation_id}"
    async with AsyncClient() as client:
        r = await client.patch(url, json={"status": status}, headers={"Authorization": auth})
        return r.json()