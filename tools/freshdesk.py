"""Safe Freshdesk API integration."""

from __future__ import annotations

import re
from typing import Any

from httpx import AsyncClient


_ACCOUNT_RE = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?")
_TICKET_ID_RE = re.compile(r"[1-9][0-9]{0,18}")
_TICKET_FILTERS = frozenset({"open", "pending", "resolved", "closed"})


def _freshdesk_base_url(account: object) -> str:
    """Return Freshdesk's API origin for one canonical account subdomain."""
    value = str(account or "").strip().lower()
    if not _ACCOUNT_RE.fullmatch(value):
        raise ValueError("Freshdesk account must be a single canonical DNS label.")
    return f"https://{value}.freshdesk.com/api/v2"


def _ticket_id(value: object) -> str:
    identifier = str(value or "").strip()
    if not _TICKET_ID_RE.fullmatch(identifier):
        raise ValueError("ticket_id must be a positive numeric identifier.")
    return identifier


def _ticket_filter(value: object) -> str:
    filter_value = str(value or "open").strip().lower()
    if filter_value not in _TICKET_FILTERS:
        raise ValueError("filter must be one of: open, pending, resolved, closed.")
    return filter_value


def _bounded_text(value: object, field_name: str, maximum: int) -> str:
    text = str(value or "")
    if not text.strip() or len(text) > maximum or "\x00" in text:
        raise ValueError(f"{field_name} must be non-empty, within {maximum} characters, and contain no null bytes.")
    return text


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _request(
    method: str,
    base_url: str,
    path: str,
    token: str,
    *,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Perform one bounded Freshdesk request without following redirects."""
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.request(
            method,
            f"{base_url}{path}",
            json=json,
            params=params,
            headers=_headers(token),
        )
        return response.json()


async def create_ticket(account: str, token: str, subject: str, description: str, email: str) -> dict[str, Any]:
    """Create a Freshdesk ticket at a validated account origin."""
    return await _request(
        "POST",
        _freshdesk_base_url(account),
        "/tickets",
        token,
        json={
            "subject": _bounded_text(subject, "subject", 500),
            "description": _bounded_text(description, "description", 65_535),
            "email": _bounded_text(email, "email", 254),
            "status": 2,
            "priority": 1,
        },
    )


async def list_tickets(account: str, token: str, filter: str = "open") -> dict[str, Any]:
    """List tickets filtered by a constrained ticket state."""
    return await _request(
        "GET",
        _freshdesk_base_url(account),
        "/tickets",
        token,
        params={"filter_type": _ticket_filter(filter)},
    )


async def get_ticket(account: str, token: str, ticket_id: int) -> dict[str, Any]:
    """Get a ticket selected by a validated numeric identifier."""
    return await _request(
        "GET",
        _freshdesk_base_url(account),
        f"/tickets/{_ticket_id(ticket_id)}",
        token,
    )


async def update_ticket(account: str, token: str, ticket_id: int, **kwargs: Any) -> dict[str, Any]:
    """Update a ticket selected by a validated numeric identifier."""
    return await _request(
        "PUT",
        _freshdesk_base_url(account),
        f"/tickets/{_ticket_id(ticket_id)}",
        token,
        json=kwargs,
    )


async def add_reply(account: str, token: str, ticket_id: int, body: str) -> dict[str, Any]:
    """Add a bounded reply to a ticket selected by a validated identifier."""
    return await _request(
        "POST",
        _freshdesk_base_url(account),
        f"/tickets/{_ticket_id(ticket_id)}/reply",
        token,
        json={"body": _bounded_text(body, "body", 65_535)},
    )
