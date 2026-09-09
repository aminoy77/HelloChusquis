"""Safe Pipedrive API integration."""

from __future__ import annotations

from typing import Any

from httpx import AsyncClient


_BASE_URL = "https://api.pipedrive.com/v1"
_DEAL_STATUSES = frozenset({"open", "won", "lost", "deleted", "all_not_deleted"})


def _deal_status(value: object) -> str:
    """Validate the Pipedrive deal status before using it as a request parameter."""
    status = str(value or "").strip().lower()
    if status not in _DEAL_STATUSES:
        raise ValueError("status must be one of: open, won, lost, deleted, all_not_deleted.")
    return status


def _bounded_text(value: object, field_name: str, maximum: int) -> str:
    text = str(value or "")
    if not text.strip() or len(text) > maximum or "\x00" in text:
        raise ValueError(f"{field_name} must be non-empty, within {maximum} characters, and contain no null bytes.")
    return text


def _headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"}


async def _request(
    method: str,
    path: str,
    api_key: str,
    *,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Perform one bounded Pipedrive request without following redirects."""
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.request(
            method,
            f"{_BASE_URL}{path}",
            json=json,
            params=params,
            headers=_headers(api_key),
        )
        return response.json()


async def create_company(name: str, api_key: str, **kwargs: Any) -> dict[str, Any]:
    """Create a company with a bounded name and explicitly supplied fields."""
    return await _request(
        "POST",
        "/companies",
        api_key,
        json={"name": _bounded_text(name, "name", 255), **kwargs},
    )


async def get_deals(api_key: str, status: str = "open") -> dict[str, Any]:
    """Get Pipedrive deals using a constrained status query parameter."""
    return await _request("GET", "/deals", api_key, params={"status": _deal_status(status)})


async def add_activity(api_key: str, subject: str, type: str, due_date: str) -> dict[str, Any]:
    """Add a bounded activity with non-empty subject, type and due date fields."""
    return await _request(
        "POST",
        "/activities",
        api_key,
        json={
            "subject": _bounded_text(subject, "subject", 500),
            "type": _bounded_text(type, "type", 100),
            "due_date": _bounded_text(due_date, "due_date", 32),
        },
    )
