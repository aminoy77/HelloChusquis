"""Safe Facebook Graph API integration."""

from __future__ import annotations

import re
from typing import Any

from httpx import AsyncClient


_BASE_URL = "https://graph.facebook.com/v18.0"
_FACEBOOK_ID_RE = re.compile(r"[1-9][0-9]{0,19}")


def _facebook_id(value: object) -> str:
    """Validate a Graph API numeric identifier before embedding it in a path."""
    identifier = str(value or "").strip()
    if not _FACEBOOK_ID_RE.fullmatch(identifier):
        raise ValueError("Facebook resource identifier must be a positive numeric identifier.")
    return identifier


def _bounded_text(value: object, field_name: str, maximum: int) -> str:
    text = str(value or "")
    if not text.strip() or len(text) > maximum or "\x00" in text:
        raise ValueError(f"{field_name} must be non-empty, within {maximum} characters, and contain no null bytes.")
    return text


def _headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


async def _request(
    method: str,
    path: str,
    access_token: str,
    *,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Perform one bounded Graph API request without following redirects."""
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.request(
            method,
            f"{_BASE_URL}{path}",
            json=json,
            params=params,
            headers=_headers(access_token),
        )
        return response.json()


async def create_page(name: str, access_token: str) -> dict[str, Any]:
    """Create a Facebook page with a bounded page name."""
    return await _request(
        "POST",
        "/me/accounts",
        access_token,
        json={"name": _bounded_text(name, "name", 255)},
    )


async def post_to_page(page_id: str, message: str, access_token: str) -> dict[str, Any]:
    """Post a bounded message to a page selected by a validated identifier."""
    return await _request(
        "POST",
        f"/{_facebook_id(page_id)}/feed",
        access_token,
        json={"message": _bounded_text(message, "message", 63_206)},
    )


async def get_page_insights(page_id: str, access_token: str) -> dict[str, Any]:
    """Get the fixed, read-only set of page insights."""
    return await _request(
        "GET",
        f"/{_facebook_id(page_id)}/insights",
        access_token,
        params={"metric": "page_fans,page_impressions"},
    )


async def send_message(recipient_id: str, message: str, access_token: str) -> dict[str, Any]:
    """Send a bounded message to a validated recipient identifier."""
    return await _request(
        "POST",
        "/me/messages",
        access_token,
        json={
            "recipient": {"id": _facebook_id(recipient_id)},
            "message": {"text": _bounded_text(message, "message", 2000)},
        },
    )
