"""Safe Greenhouse Job Board and Harvest API integration."""

from __future__ import annotations

import re
from typing import Any

import httpx


_JOB_BOARD_BASE_URL = "https://boards-api.greenhouse.io/v1/boards"
_HARVEST_BASE_URL = "https://harvest.greenhouse.io/v1"
_BOARD_TOKEN_RE = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,126}[a-z0-9])?")
_ID_RE = re.compile(r"[1-9][0-9]{0,18}")
_EMAIL_RE = re.compile(
    r"[A-Za-z0-9.!#$%&'*+=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+"
)


def _board_token(value: object) -> str:
    """Validate a Greenhouse Job Board token before embedding it in a path."""
    token = str(value or "").strip().lower()
    if not _BOARD_TOKEN_RE.fullmatch(token):
        raise ValueError("board_token must be a single canonical Job Board identifier.")
    return token


def _greenhouse_id(value: object, field_name: str) -> str:
    identifier = str(value or "").strip()
    if not _ID_RE.fullmatch(identifier):
        raise ValueError(f"{field_name} must be a positive numeric identifier.")
    return identifier


def _email(value: object) -> str:
    email = str(value or "").strip()
    if len(email) > 254 or not _EMAIL_RE.fullmatch(email):
        raise ValueError("A valid candidate email is required.")
    return email


def _name(value: object, field_name: str) -> str:
    name = str(value or "").strip()
    if not name or len(name) > 255 or any(char in name for char in "\r\n\x00"):
        raise ValueError(f"{field_name} must be non-empty and cannot contain control characters.")
    return name


def _harvest_auth(api_key: str) -> httpx.BasicAuth:
    """Build Harvest's documented Basic Auth credential (token as username, blank password)."""
    if not api_key:
        raise ValueError("A Greenhouse Harvest API key is required.")
    return httpx.BasicAuth(api_key, "")


async def _request(
    method: str,
    url: str,
    *,
    auth: httpx.Auth | None = None,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Perform one bounded request without following redirects."""
    async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.request(method, url, auth=auth, params=params, json=json)
        return response.json()


async def list_jobs(board_token: str) -> dict[str, Any]:
    """List public jobs from the specified validated Job Board."""
    return await _request("GET", f"{_JOB_BOARD_BASE_URL}/{_board_token(board_token)}/jobs")


async def get_job(board_token: str, job_id: str) -> dict[str, Any]:
    """Get a public job from a validated board and numeric job identifier."""
    return await _request(
        "GET",
        f"{_JOB_BOARD_BASE_URL}/{_board_token(board_token)}/jobs/{_greenhouse_id(job_id, 'job_id')}",
    )


async def list_candidates(api_key: str, job_id: str | None = None) -> dict[str, Any]:
    """List Harvest candidates, optionally constrained to a validated job identifier."""
    params: dict[str, Any] = {"per_page": 50}
    if job_id is not None:
        params["job_id"] = _greenhouse_id(job_id, "job_id")
    return await _request(
        "GET",
        f"{_HARVEST_BASE_URL}/candidates",
        auth=_harvest_auth(api_key),
        params=params,
    )


async def create_candidate(api_key: str, email: str, first_name: str, last_name: str) -> dict[str, Any]:
    """Create a candidate using the Harvest API's documented Basic Auth model."""
    return await _request(
        "POST",
        f"{_HARVEST_BASE_URL}/candidates",
        auth=_harvest_auth(api_key),
        json={
            "email": _email(email),
            "first_name": _name(first_name, "first_name"),
            "last_name": _name(last_name, "last_name"),
        },
    )
