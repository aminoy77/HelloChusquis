from  httpx import AsyncClient
from  json import dumps
from  typing import Any
from typing_extensions import TypedDict


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