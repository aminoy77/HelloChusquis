"""Safe LinkedIn API integration."""

from __future__ import annotations

import re
from typing import Any

from httpx import AsyncClient


_BASE_URL = "https://api.linkedin.com/v2"
_PROFILE_ID_RE = re.compile(r"[A-Za-z0-9_-]{1,128}")
_RECIPIENT_RE = re.compile(r"[A-Za-z0-9:_-]{1,256}")


def _profile_id(value: object) -> str:
    """Validate a profile identifier before embedding it in a LinkedIn API path."""
    identifier = str(value or "").strip()
    if identifier == "me":
        return identifier
    if not _PROFILE_ID_RE.fullmatch(identifier):
        raise ValueError("person_id must be 'me' or a single safe identifier.")
    return identifier


def _recipient_id(value: object) -> str:
    recipient = str(value or "").strip()
    if not _RECIPIENT_RE.fullmatch(recipient):
        raise ValueError("recipient must be a single safe LinkedIn identifier or URN.")
    return recipient


def _bounded_text(value: object, field_name: str, maximum: int) -> str:
    text = str(value or "").strip()
    if not text or len(text) > maximum or any(char in text for char in "\r\n\x00"):
        raise ValueError(f"{field_name} must be non-empty, within {maximum} characters, and contain no control characters.")
    return text


def _headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"}


async def _request(
    method: str,
    path: str,
    api_key: str,
    *,
    json_data: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Perform one bounded LinkedIn API request without following redirects."""
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.request(
            method,
            f"{_BASE_URL}{path}",
            json=json_data,
            params=params,
            headers=_headers(api_key),
        )
        return response.json()


async def post_job(title: str, location: str, api_key: str, **kwargs: Any) -> dict[str, Any]:
    """Post a job with bounded title and location fields."""
    return await _request(
        "POST",
        "/jobs",
        api_key,
        json_data={
            "title": _bounded_text(title, "title", 500),
            "location": _bounded_text(location, "location", 500),
            **kwargs,
        },
    )


async def search_jobs(api_key: str, keywords: str) -> dict[str, Any]:
    """Search jobs with structured query parameters."""
    return await _request(
        "GET",
        "/jobs",
        api_key,
        params={"keywords": _bounded_text(keywords, "keywords", 1000)},
    )


async def get_profile(api_key: str, person_id: str = "me") -> dict[str, Any]:
    """Get a profile selected by a validated identifier."""
    return await _request("GET", f"/people/{_profile_id(person_id)}", api_key)


async def share_post(api_key: str, comment: str, title: str | None = None) -> dict[str, Any]:
    """Share a bounded post; omit optional content rather than sending JSON null."""
    payload: dict[str, Any] = {"comment": _bounded_text(comment, "comment", 3000)}
    if title is not None:
        payload["content"] = {"title": {"text": _bounded_text(title, "title", 500)}}
    return await _request("POST", "/ugcPosts", api_key, json_data=payload)


async def send_message(api_key: str, recipient: str, message: str) -> dict[str, Any]:
    """Send a bounded message to a validated recipient identifier."""
    return await _request(
        "POST",
        "/messages",
        api_key,
        json_data={
            "recipients": [_recipient_id(recipient)],
            "message": {"body": _bounded_text(message, "message", 8000)},
        },
    )
