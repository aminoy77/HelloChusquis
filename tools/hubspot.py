from httpx import AsyncClient
import os
import re
from urllib.parse import quote

import httpx


_EMAIL_RE = re.compile(
    r"[A-Za-z0-9.!#$%&'*+=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+"
)


def _contact_email_path_segment(email: object) -> str:
    """Validate a HubSpot contact email and encode it as exactly one path segment."""
    value = str(email or "").strip()
    if len(value) > 254 or not _EMAIL_RE.fullmatch(value):
        raise ValueError("A valid contact email is required.")
    return quote(value, safe="")


def run(action: str, **kwargs) -> str:
    """Synchronous dispatcher for HubSpot API actions."""
    api_key = kwargs.get("api_key") or os.getenv("HUBSPOT_API_KEY")
    if not api_key:
        return "Error: No HubSpot API key found. Set HUBSPOT_API_KEY environment variable."

    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return _run_sync(action, api_key, kwargs)
        return loop.run_until_complete(_run_async(action, api_key, kwargs))
    except RuntimeError:
        return _run_sync(action, api_key, kwargs)


async def _run_async(action: str, api_key: str, kwargs: dict) -> str:
    """Async dispatcher for HubSpot operations."""
    if action == "create_lead":
        return str(await create_lead(kwargs.get("email", ""), kwargs.get("first_name", ""), kwargs.get("last_name", ""), api_key))[:2000]
    elif action == "get_lead":
        return str(await get_lead(kwargs.get("email", ""), api_key))[:2000]
    elif action == "create_deal":
        return str(await create_deal(kwargs.get("name", ""), kwargs.get("amount", ""), kwargs.get("stage", ""), api_key))[:2000]
    elif action == "create_company":
        return str(await create_company(kwargs.get("domain", ""), kwargs.get("name", ""), api_key))[:2000]
    else:
        return f"Error: Unknown action '{action}'. Available: create_lead, get_lead, create_deal, create_company"


def _run_sync(action: str, api_key: str, kwargs: dict) -> str:
    """Synchronous fallback using httpx.Client."""
    base_url = "https://api.hubapi.com"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        client = httpx.Client(timeout=30, follow_redirects=False)
        if action == "create_lead":
            r = client.post(f"{base_url}/crm/v3/objects/contacts",
                           json={"properties": {"email": kwargs.get("email", ""), "firstname": kwargs.get("first_name", ""), "lastname": kwargs.get("last_name", "")}},
                           headers=headers)
            return str(r.json())[:2000]
        elif action == "get_lead":
            contact_email = _contact_email_path_segment(kwargs.get("email", ""))
            r = client.get(
                f"{base_url}/crm/v3/objects/contacts/{contact_email}",
                headers=headers,
                params={"idProperty": "email"},
            )
            return str(r.json())[:2000]
        elif action == "create_deal":
            r = client.post(f"{base_url}/crm/v3/objects/deals",
                           json={"properties": {"dealname": kwargs.get("name", ""), "amount": kwargs.get("amount", ""), "dealstage": kwargs.get("stage", "")}},
                           headers=headers)
            return str(r.json())[:2000]
        elif action == "create_company":
            r = client.post(f"{base_url}/crm/v3/objects/companies",
                           json={"properties": {"domain": kwargs.get("domain", ""), "name": kwargs.get("name", "")}},
                           headers=headers)
            return str(r.json())[:2000]
        else:
            return f"Error: Unknown action '{action}'. Available: create_lead, get_lead, create_deal, create_company"
    except Exception as e:
        return f"Error: {str(e)}"


async def create_lead(email: str, first_name: str, last_name: str, api_key: str) -> dict:
    """Create HubSpot lead."""
    url = "https://api.hubapi.com/crm/v3/objects/contacts"
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        r = await client.post(url, json={"properties": {"email": email, "firstname": first_name, "lastname": last_name}}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def get_lead(email: str, api_key: str) -> dict:
    """Get HubSpot contact."""
    contact_email = _contact_email_path_segment(email)
    url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_email}"
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        r = await client.get(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            params={"idProperty": "email"},
        )
        return r.json()


async def create_deal(name: str, amount: str, stage: str, api_key: str) -> dict:
    """Create HubSpot deal."""
    url = "https://api.hubapi.com/crm/v3/objects/deals"
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        r = await client.post(url, json={"properties": {"dealname": name, "amount": amount, "dealstage": stage}}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def create_company(domain: str, name: str, api_key: str) -> dict:
    """Create HubSpot company."""
    url = "https://api.hubapi.com/crm/v3/objects/companies"
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        r = await client.post(url, json={"properties": {"domain": domain, "name": name}}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()