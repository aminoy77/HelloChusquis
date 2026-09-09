"""Safe Zendesk API integration."""

from __future__ import annotations

import re
from typing import Any

from httpx import AsyncClient


_SUBDOMAIN_RE = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?")


def _zendesk_base_url(subdomain: object) -> str:
    """Return the Zendesk API origin for one canonical account subdomain."""
    value = str(subdomain or "").strip().lower()
    if not _SUBDOMAIN_RE.fullmatch(value):
        raise ValueError("Zendesk subdomain must be a single canonical DNS label.")
    return f"https://{value}.zendesk.com/api/v2"


def _ticket_id(value: object, field_name: str = "ticket_id") -> str:
    """Validate a Zendesk numeric resource identifier before placing it in a path."""
    text = str(value or "").strip()
    if not re.fullmatch(r"[1-9][0-9]{0,18}", text):
        raise ValueError(f"{field_name} must be a positive numeric identifier.")
    return text


def _bounded_per_page(value: object, default: int = 100) -> int:
    try:
        per_page = int(value)
    except (TypeError, ValueError):
        per_page = default
    return max(1, min(per_page, 100))


async def _request(
    method: str,
    base_url: str,
    path: str,
    api_key: str,
    *,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Perform one bounded Zendesk request without following redirects."""
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.request(
            method,
            f"{base_url}{path}",
            json=json,
            params=params,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        return response.json()


async def create_ticket(
    api_key: str,
    subdomain: str,
    subject: str,
    description: str,
    requester: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Create a Zendesk ticket at a validated account origin."""
    return await _request(
        "POST",
        _zendesk_base_url(subdomain),
        "/tickets.json",
        api_key,
        json={
            "ticket": {
                "subject": subject,
                "description": description,
                "requester": {"email": requester},
                **kwargs,
            }
        },
    )


async def list_tickets(api_key: str, subdomain: str, per_page: int = 100) -> dict[str, Any]:
    """List a bounded page of Zendesk tickets."""
    return await _request(
        "GET",
        _zendesk_base_url(subdomain),
        "/tickets.json",
        api_key,
        params={"per_page": _bounded_per_page(per_page)},
    )


async def update_ticket(
    api_key: str,
    subdomain: str,
    ticket_id: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Update a ticket selected by a validated numeric identifier."""
    return await _request(
        "PUT",
        _zendesk_base_url(subdomain),
        f"/tickets/{_ticket_id(ticket_id)}.json",
        api_key,
        json={"ticket": kwargs},
    )


async def search_tickets(
    api_key: str,
    subdomain: str,
    query: str,
    per_page: int = 100,
) -> dict[str, Any]:
    """Search tickets with structured query parameters and a bounded page size."""
    return await _request(
        "GET",
        _zendesk_base_url(subdomain),
        "/search.json",
        api_key,
        params={"query": str(query or "")[:4096], "per_page": _bounded_per_page(per_page)},
    )


async def add_comment(
    api_key: str,
    subdomain: str,
    ticket_id: str,
    body: str,
    author_id: str,
) -> dict[str, Any]:
    """Add a comment to a ticket with validated resource identifiers."""
    return await _request(
        "PUT",
        _zendesk_base_url(subdomain),
        f"/tickets/{_ticket_id(ticket_id)}.json",
        api_key,
        json={
            "ticket": {
                "comment": {
                    "body": str(body or "")[:65535],
                    "author_id": int(_ticket_id(author_id, "author_id")),
                }
            }
        },
    )
