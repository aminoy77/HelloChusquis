from  httpx import AsyncClient
from  json import dumps
from  typing import Any
from typing_extensions import TypedDict
import os
import httpx


def run(action: str, **kwargs) -> str:
    """Synchronous dispatcher for Mailchimp API actions."""
    api_key = kwargs.get("api_key") or os.getenv("MAILCHIMP_API_KEY")
    server = kwargs.get("server") or os.getenv("MAILCHIMP_SERVER")
    if not api_key or not server:
        return "Error: No Mailchimp credentials found. Set MAILCHIMP_API_KEY and MAILCHIMP_SERVER environment variables."

    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return _run_sync(action, api_key, server, kwargs)
        return loop.run_until_complete(_run_async(action, api_key, server, kwargs))
    except RuntimeError:
        return _run_sync(action, api_key, server, kwargs)


async def _run_async(action: str, api_key: str, server: str, kwargs: dict) -> str:
    """Async dispatcher for Mailchimp operations."""
    if action == "add_subscriber":
        return await add_subscriber(api_key, server, kwargs.get("list_id", ""), kwargs.get("email", ""), **{k: v for k, v in kwargs.items() if k not in ("api_key", "server", "list_id", "email")})
    elif action == "remove_subscriber":
        return await remove_subscriber(api_key, server, kwargs.get("list_id", ""), kwargs.get("email", ""))
    elif action == "get_lists":
        return await get_lists(api_key, server)
    elif action == "get_campaigns":
        return await get_campaigns(api_key, server)
    elif action == "send_campaign":
        return await send_campaign(api_key, server, kwargs.get("campaign_id", ""))
    else:
        return f"Error: Unknown action '{action}'. Available: add_subscriber, remove_subscriber, get_lists, get_campaigns, send_campaign"


def _run_sync(action: str, api_key: str, server: str, kwargs: dict) -> str:
    """Synchronous fallback using httpx.Client."""
    base_url = f"https://{server}.api.mailchimp.com/3.0"
    headers = {"Authorization": f"apikey {api_key}"}

    try:
        client = httpx.Client(timeout=30)
        if action == "add_subscriber":
            list_id = kwargs.get("list_id", "")
            r = client.post(f"{base_url}/lists/{list_id}/members", json={"email_address": kwargs.get("email", ""), "status": "subscribed"}, headers=headers)
            return str(r.json())[:2000]
        elif action == "remove_subscriber":
            list_id = kwargs.get("list_id", "")
            email = kwargs.get("email", "")
            r = client.delete(f"{base_url}/lists/{list_id}/members/{email}", headers=headers)
            return str(r.json())[:2000]
        elif action == "get_lists":
            r = client.get(f"{base_url}/lists", headers=headers)
            return str(r.json())[:2000]
        elif action == "get_campaigns":
            r = client.get(f"{base_url}/campaigns", headers=headers)
            return str(r.json())[:2000]
        elif action == "send_campaign":
            campaign_id = kwargs.get("campaign_id", "")
            r = client.post(f"{base_url}/campaigns/{campaign_id}/actions/send", headers=headers)
            return str(r.json())[:2000]
        else:
            return f"Error: Unknown action '{action}'. Available: add_subscriber, remove_subscriber, get_lists, get_campaigns, send_campaign"
    except Exception as e:
        return f"Error: {str(e)}"


class Mailchimp(TypedDict):
    api_key: str
    server: str


async def add_subscriber(api_key: str, server: str, list_id: str, email: str, **kwargs) -> dict:
    """Add subscriber to Mailchimp list."""
    url = f"https://{server}.api.mailchimp.com/3.0/lists/{list_id}/members"
    async with AsyncClient() as client:
        r = await client.post(url, json={
            "email_address": email,
            "status": "subscribed",
            **kwargs
        }, headers={"Authorization": f"apikey {api_key}"})
        return r.json()


async def remove_subscriber(api_key: str, server: str, list_id: str, email: str) -> dict:
    """Remove subscriber from Mailchimp list."""
    url = f"https://{server}.api.mailchimp.com/3.0/lists/{list_id}/members/{hash(email)}"
    async with AsyncClient() as client:
        r = await client.delete(url, headers={"Authorization": f"apikey {api_key}"})
        return {"status": "deleted"}


async def get_lists(api_key: str, server: str) -> dict:
    """Get Mailchimp lists."""
    url = f"https://{server}.api.mailchimp.com/3.0/lists"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"apikey {api_key}"})
        return r.json()


async def get_campaigns(api_key: str, server: str) -> dict:
    """Get Mailchimp campaigns."""
    url = f"https://{server}.api.mailchimp.com/3.0/campaigns"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"apikey {api_key}"})
        return r.json()


async def send_campaign(api_key: str, server: str, campaign_id: str) -> dict:
    """Send Mailchimp campaign."""
    url = f"https://{server}.api.mailchimp.com/3.0/campaigns/{campaign_id}/actions/send"
    async with AsyncClient() as client:
        r = await client.post(url, headers={"Authorization": f"apikey {api_key}"})
        return {"status": "sent"}