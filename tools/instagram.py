"""Safe Instagram Graph API integration."""

from __future__ import annotations

import re
from urllib.parse import urlsplit

from httpx import AsyncClient


_BASE_URL = "https://graph.facebook.com/v18.0"
_INSTAGRAM_ID_RE = re.compile(r"[1-9][0-9]{0,19}")


def _instagram_id(value: object) -> str:
    """Validate a Graph API resource identifier before embedding it in a path."""
    identifier = str(value or "").strip()
    if not _INSTAGRAM_ID_RE.fullmatch(identifier):
        raise ValueError("Instagram resource identifier must be a positive numeric identifier.")
    return identifier


def _media_url(value: object) -> str:
    """Validate a public HTTPS media URL submitted to the remote Graph API."""
    url = str(value or "").strip()
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or any(char in url for char in "\r\n\x00")
    ):
        raise ValueError("media_url must be an HTTPS URL without credentials or control characters.")
    return url


def _caption(value: object) -> str:
    caption = str(value or "")
    if len(caption) > 2200 or "\x00" in caption:
        raise ValueError("caption must contain at most 2,200 characters and no null bytes.")
    return caption


def _bounded_limit(value: object, default: int = 10) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError):
        limit = default
    return max(1, min(limit, 100))


def _headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"}


async def _request(
    method: str,
    path: str,
    api_key: str,
    *,
    json: dict[str, object] | None = None,
    params: dict[str, object] | None = None,
) -> dict:
    """Perform a bounded Graph API request without following redirects."""
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.request(
            method,
            f"{_BASE_URL}{path}",
            json=json,
            params=params,
            headers=_headers(api_key),
        )
        return response.json()


async def post_media(media_url: str, caption: str, api_key: str) -> dict:
    """Create an Instagram media container from a validated HTTPS image URL."""
    return await _request(
        "POST",
        "/me/media",
        api_key,
        json={"media_type": "IMAGE", "image_url": _media_url(media_url), "caption": _caption(caption)},
    )


async def publish_media(creation_id: str, api_key: str) -> dict:
    """Publish a validated media container identifier."""
    return await _request(
        "POST",
        "/me/media_publish",
        api_key,
        json={"creation_id": _instagram_id(creation_id)},
    )


async def get_media(api_key: str, limit: int = 10) -> dict:
    """Get a bounded number of Instagram media objects."""
    return await _request("GET", "/me/media", api_key, params={"limit": _bounded_limit(limit)})


async def get_insights(media_id: str, api_key: str) -> dict:
    """Get insights for a media object selected by a validated identifier."""
    return await _request("GET", f"/{_instagram_id(media_id)}/insights", api_key)


async def get_user_insights(api_key: str) -> dict:
    """Get the fixed, read-only set of account insight metrics."""
    return await _request(
        "GET",
        "/me/insights",
        api_key,
        params={"metric": "impressions,reach,follower_count"},
    )
