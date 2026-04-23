from httpx import AsyncClient


async def create_conversation(token: str, from_: str, body: str, **kwargs) -> dict:
    """Create Intercom conversation."""
    url = "https://api.intercom.io/conversations"
    async with AsyncClient() as client:
        r = await client.post(url, json={
            "from": {"type": "user", "email": from_},
            "body": body, **kwargs
        }, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
        return r.json()


async def list_conversations(token: str, state: str = "open") -> dict:
    """List Intercom conversations."""
    url = f"https://api.intercom.io/conversations?state={state}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
        return r.json()


async def get_conversation(token: str, conversation_id: str) -> dict:
    """Get Intercom conversation."""
    url = f"https://api.intercom.io/conversations/{conversation_id}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
        return r.json()


async def reply_conversation(token: str, conversation_id: str, message_type: str, body: str) -> dict:
    """Reply to Intercom conversation."""
    url = f"https://api.intercom.io/conversations/{conversation_id}/reply"
    async with AsyncClient() as client:
        r = await client.post(url, json={"message_type": message_type, "type": "user", "body": body}, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
        return r.json()


async def update_conversation(token: str, conversation_id: str, **kwargs) -> dict:
    """Update Intercom conversation."""
    url = f"https://api.intercom.io/conversations/{conversation_id}"
    async with AsyncClient() as client:
        r = await client.put(url, json=kwargs, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
        return r.json()