"""Bounded ActiveCampaign API helpers."""

from __future__ import annotations

from urllib.parse import quote

from httpx import AsyncClient

MAX_CONTACTS = 100


def _contact_path(email: object) -> str:
    value = str(email or "")
    if not value or len(value) > 320 or "\r" in value or "\n" in value:
        raise ValueError("Invalid ActiveCampaign contact email.")
    return quote(value, safe="")


def _limit(value: object) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return MAX_CONTACTS
    return max(1, min(limit, MAX_CONTACTS))


async def add_contact(api_key: str, email: str, **properties) -> dict:
    """Add or synchronize a contact."""
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.post(
            "https://api.activecampaign.com/api/3/contact/sync",
            json={"contact": {"email": email, **properties}},
            headers={"Api-Key": api_key},
        )
        response.raise_for_status()
        return response.json()


async def get_contact(api_key: str, email: str) -> dict:
    """Fetch a contact by safely encoded email segment."""
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.get(
            f"https://api.activecampaign.com/api/3/contact/{_contact_path(email)}",
            headers={"Api-Key": api_key},
        )
        response.raise_for_status()
        return response.json()


async def list_contacts(api_key: str, limit: int = MAX_CONTACTS) -> dict:
    """List a bounded number of contacts."""
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.get(
            "https://api.activecampaign.com/api/3/contacts",
            params={"limit": _limit(limit)},
            headers={"Api-Key": api_key},
        )
        response.raise_for_status()
        return response.json()


async def create_deal(api_key: str, name: str, value: float, stage: str = "1") -> dict:
    """Create a deal."""
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.post(
            "https://api.activecampaign.com/api/3/deals",
            json={"deal": {"name": name, "value": value, "stage": stage}},
            headers={"Api-Key": api_key},
        )
        response.raise_for_status()
        return response.json()


async def update_contact_field(api_key: str, email: str, field: str, value: str) -> dict:
    """Update a custom contact field."""
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.post(
            "https://api.activecampaign.com/api/3/field/sync",
            json={"contact": {"email": email, "fieldValues": [{"field": field, "value": value}]}},
            headers={"Api-Key": api_key},
        )
        response.raise_for_status()
        return response.json()
