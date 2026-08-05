from httpx import AsyncClient
import os
import httpx


def run(action: str, **kwargs) -> str:
    """Synchronous dispatcher for Intercom API actions."""
    token = kwargs.get("token") or os.getenv("INTERCOM_ACCESS_TOKEN")
    if not token:
        return "Error: No Intercom token found. Set INTERCOM_ACCESS_TOKEN environment variable."

    import asyncio
    try:
        loop = asyncio.get_running_loop()
        import concurrent.futures
        fut = asyncio.run_coroutine_threadsafe(_run_async(action, token, kwargs), loop)
        return fut.result(timeout=30)
    except RuntimeError:
        return _run_sync(action, token, kwargs)


async def _run_async(action: str, token: str, kwargs: dict) -> str:
    """Async dispatcher for Intercom operations."""
    if action == "create_conversation":
        return str(await create_conversation(token, kwargs.get("from_", ""), kwargs.get("body", ""), **kwargs))[2000]
    elif action == "list_conversations":
        return str(await list_conversations(token, kwargs.get("state", "open")))[2000]
    elif action == "get_conversation":
        return str(await get_conversation(token, kwargs.get("conversation_id", "")))[:2000]
    elif action == "reply_conversation":
        return str(await reply_conversation(token, kwargs.get("conversation_id", ""), kwargs.get("message_type", ""), kwargs.get("body", "")))[:2000]
    elif action == "update_conversation":
        return str(await update_conversation(token, kwargs.get("conversation_id", ""), **kwargs))[:2000]
    else:
        return f"Error: Unknown action '{action}'. Available: create_conversation, list_conversations, get_conversation, reply_conversation, update_conversation"


def _run_sync(action: str, token: str, kwargs: dict) -> str:
    """Synchronous fallback using httpx.Client."""
    base_url = "https://api.intercom.io"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    try:
        client = httpx.Client(timeout=30)
        if action == "create_conversation":
            r = client.post(f"{base_url}/conversations", json={
                "from": {"type": "user", "email": kwargs.get("from_", "")},
                "body": kwargs.get("body", "")
            }, headers=headers)
            return str(r.json())[:2000]
        elif action == "list_conversations":
            r = client.get(f"{base_url}/conversations?state={kwargs.get('state', 'open')}", headers=headers)
            return str(r.json())[:2000]
        elif action == "get_conversation":
            r = client.get(f"{base_url}/conversations/{kwargs.get('conversation_id', '')}", headers=headers)
            return str(r.json())[:2000]
        elif action == "reply_conversation":
            r = client.post(f"{base_url}/conversations/{kwargs.get('conversation_id', '')}/reply",
                           json={"message_type": kwargs.get("message_type", ""), "type": "user", "body": kwargs.get("body", "")}, headers=headers)
            return str(r.json())[:2000]
        elif action == "update_conversation":
            r = client.put(f"{base_url}/conversations/{kwargs.get('conversation_id', '')}",
                          json=kwargs, headers=headers)
            return str(r.json())[:2000]
        else:
            return f"Error: Unknown action '{action}'. Available: create_conversation, list_conversations, get_conversation, reply_conversation, update_conversation"
    except Exception as e:
        return f"Error: {str(e)}"


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