"""Safe Lever Postings API integration."""

from __future__ import annotations

import re
from typing import Any

from httpx import AsyncClient


_BASE_URL = "https://api.lever.co/v0/postings"
_SITE_RE = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,126}[a-z0-9])?")
_POSTING_ID_RE = re.compile(r"[A-Za-z0-9_-]{1,128}")
_POSTING_MODES = frozenset({"json", "html", "iframe"})


def _site(value: object) -> str:
    """Validate the Lever site token before embedding it in an API path."""
    site = str(value or "").strip().lower()
    if not _SITE_RE.fullmatch(site):
        raise ValueError("site must be a single canonical Lever site identifier.")
    return site


def _posting_id(value: object) -> str:
    """Validate a Lever posting identifier before embedding it in an API path."""
    identifier = str(value or "").strip()
    if not _POSTING_ID_RE.fullmatch(identifier):
        raise ValueError("posting_id must be a single safe path segment.")
    return identifier


def _posting_mode(value: object) -> str:
    mode = str(value or "json").strip().lower()
    if mode not in _POSTING_MODES:
        raise ValueError("mode must be one of: json, html, iframe.")
    return mode


def _bounded_integer(value: object, field_name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    if number < minimum or number > maximum:
        raise ValueError(f"{field_name} must be between {minimum} and {maximum}.")
    return number


async def _request(path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Read a Lever public posting response with explicit limits and no redirects."""
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.get(
            f"{_BASE_URL}{path}",
            params=params,
            headers={"Accept": "application/json"},
        )
        return response.json()


async def list_jobs(site: str, limit: int = 100, skip: int = 0) -> dict[str, Any]:
    """List a bounded page of public job postings for a validated company site."""
    return await _request(
        f"/{_site(site)}",
        params={
            "mode": "json",
            "limit": _bounded_integer(limit, "limit", 100, 1, 100),
            "skip": _bounded_integer(skip, "skip", 0, 0, 10_000),
        },
    )


async def get_job(site: str, job_id: str) -> dict[str, Any]:
    """Get one public posting for a validated Lever site and posting identifier."""
    return await _request(f"/{_site(site)}/{_posting_id(job_id)}")


async def list_stages(api_key: str, job_id: str) -> dict[str, Any]:
    """Reject the undocumented legacy stages route instead of issuing an invalid request."""
    del api_key, job_id
    raise ValueError("The public Lever Postings API does not expose hiring stages.")


async def get_postings(site: str, mode: str = "json", limit: int = 100, skip: int = 0) -> dict[str, Any]:
    """Get public postings in a constrained documented rendering mode."""
    return await _request(
        f"/{_site(site)}",
        params={
            "mode": _posting_mode(mode),
            "limit": _bounded_integer(limit, "limit", 100, 1, 100),
            "skip": _bounded_integer(skip, "skip", 0, 0, 10_000),
        },
    )
