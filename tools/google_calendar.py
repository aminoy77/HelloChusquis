"""Safe Google Calendar API integration."""

from __future__ import annotations

import asyncio
import os
import re
from typing import Any

import httpx


_BASE_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
_EVENT_ID_RE = re.compile(r"[A-Za-z0-9_-]{1,1024}")


def _event_id(value: object) -> str:
    """Validate an event identifier before embedding it in a Calendar API path."""
    identifier = str(value or "").strip()
    if not _EVENT_ID_RE.fullmatch(identifier):
        raise ValueError("event_id must be a single safe identifier.")
    return identifier


def _bounded_max_results(value: object, default: int = 10) -> int:
    try:
        max_results = int(value)
    except (TypeError, ValueError):
        max_results = default
    return max(1, min(max_results, 2500))


def _event_datetime(value: object, field_name: str) -> str:
    timestamp = str(value or "").strip()
    if not timestamp or len(timestamp) > 128 or any(char in timestamp for char in "\r\n"):
        raise ValueError(f"{field_name} must be a non-empty ISO 8601 datetime.")
    return timestamp


def _clean_fields(kwargs: dict[str, Any], *excluded: str) -> dict[str, Any]:
    blocked = {"action", "api_key", *excluded}
    return {key: value for key, value in kwargs.items() if key not in blocked}


def _headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"}


async def _request(
    method: str,
    url: str,
    api_key: str,
    *,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    expect_json: bool = True,
) -> dict[str, Any]:
    """Perform one bounded redirect-free Calendar API request."""
    async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.request(method, url, json=json, params=params, headers=_headers(api_key))
        if expect_json:
            return response.json()
        return {"deleted": response.is_success}


async def create_event(
    summary: str,
    start: str,
    end: str,
    api_key: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Create a Calendar event with required, non-empty start and end times."""
    return await _request(
        "POST",
        _BASE_URL,
        api_key,
        json={
            "summary": str(summary or "")[:1024],
            "start": {"dateTime": _event_datetime(start, "start")},
            "end": {"dateTime": _event_datetime(end, "end")},
            **_clean_fields(kwargs, "summary", "start", "end"),
        },
    )


async def list_events(api_key: str, max_results: int = 10) -> dict[str, Any]:
    """List a bounded number of Calendar events."""
    return await _request(
        "GET",
        _BASE_URL,
        api_key,
        params={"maxResults": _bounded_max_results(max_results)},
    )


async def get_event(event_id: str, api_key: str) -> dict[str, Any]:
    """Get an event selected by a safe identifier."""
    return await _request("GET", f"{_BASE_URL}/{_event_id(event_id)}", api_key)


async def update_event(event_id: str, summary: str, api_key: str) -> dict[str, Any]:
    """Update the summary of an event selected by a safe identifier."""
    return await _request(
        "PATCH",
        f"{_BASE_URL}/{_event_id(event_id)}",
        api_key,
        json={"summary": str(summary or "")[:1024]},
    )


async def delete_event(event_id: str, api_key: str) -> dict[str, Any]:
    """Delete an event selected by a safe identifier."""
    return await _request(
        "DELETE",
        f"{_BASE_URL}/{_event_id(event_id)}",
        api_key,
        expect_json=False,
    )


def run(action: str, **kwargs: Any) -> str:
    """Synchronous dispatcher for Google Calendar API actions."""
    api_key = kwargs.get("api_key") or os.getenv("GOOGLE_CALENDAR_API_KEY")
    if not api_key:
        return "Error: No Google Calendar API key found. Set GOOGLE_CALENDAR_API_KEY environment variable."
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return _run_sync(action, str(api_key), kwargs)
        return loop.run_until_complete(_run_async(action, str(api_key), kwargs))
    except RuntimeError:
        return _run_sync(action, str(api_key), kwargs)


async def _run_async(action: str, api_key: str, kwargs: dict[str, Any]) -> str:
    """Async dispatcher for Google Calendar operations."""
    if action == "create_event":
        result = await create_event(
            kwargs.get("summary", ""),
            kwargs.get("start", ""),
            kwargs.get("end", ""),
            api_key,
            **_clean_fields(kwargs, "summary", "start", "end"),
        )
    elif action == "list_events":
        result = await list_events(api_key, kwargs.get("max_results", 10))
    elif action == "get_event":
        result = await get_event(kwargs.get("event_id", ""), api_key)
    elif action == "update_event":
        result = await update_event(kwargs.get("event_id", ""), kwargs.get("summary", ""), api_key)
    elif action == "delete_event":
        result = await delete_event(kwargs.get("event_id", ""), api_key)
    else:
        return "Error: Unknown action '{}'. Available: create_event, list_events, get_event, update_event, delete_event".format(action)
    return str(result)[:2000]


def _run_sync(action: str, api_key: str, kwargs: dict[str, Any]) -> str:
    """Synchronous fallback using a redirect-free, bounded HTTP client."""
    try:
        with httpx.Client(timeout=30, follow_redirects=False) as client:
            if action == "create_event":
                response = client.post(
                    _BASE_URL,
                    json={
                        "summary": str(kwargs.get("summary", ""))[:1024],
                        "start": {"dateTime": _event_datetime(kwargs.get("start", ""), "start")},
                        "end": {"dateTime": _event_datetime(kwargs.get("end", ""), "end")},
                        **_clean_fields(kwargs, "summary", "start", "end"),
                    },
                    headers=_headers(api_key),
                )
            elif action == "list_events":
                response = client.get(
                    _BASE_URL,
                    params={"maxResults": _bounded_max_results(kwargs.get("max_results", 10))},
                    headers=_headers(api_key),
                )
            elif action == "get_event":
                response = client.get(
                    f"{_BASE_URL}/{_event_id(kwargs.get('event_id', ''))}",
                    headers=_headers(api_key),
                )
            elif action == "update_event":
                response = client.patch(
                    f"{_BASE_URL}/{_event_id(kwargs.get('event_id', ''))}",
                    json={"summary": str(kwargs.get("summary", ""))[:1024]},
                    headers=_headers(api_key),
                )
            elif action == "delete_event":
                response = client.delete(
                    f"{_BASE_URL}/{_event_id(kwargs.get('event_id', ''))}",
                    headers=_headers(api_key),
                )
                return str({"deleted": response.is_success})[:2000]
            else:
                return "Error: Unknown action '{}'. Available: create_event, list_events, get_event, update_event, delete_event".format(action)
            return str(response.json())[:2000]
    except (ValueError, httpx.HTTPError) as exc:
        return f"Error: {exc}"
