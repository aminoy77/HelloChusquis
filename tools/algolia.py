"""Safe, bounded Algolia search and indexing integration."""

from __future__ import annotations

import json
import os
import re
from urllib.parse import quote, urlencode

import httpx

PLUGIN_NAME = "algolia"
PLUGIN_DESCRIPTION = "Algolia - search and analytics"
MAX_ALGOLIA_HITS = 100
MAX_ALGOLIA_QUERY_CHARS = 2_048
MAX_ALGOLIA_PAYLOAD_BYTES = 65_536
_APP_ID_RE = re.compile(r"^[A-Za-z0-9]{1,64}$")


def _app_id(value: object) -> str:
    app_id = str(value or "")
    if not _APP_ID_RE.fullmatch(app_id):
        raise ValueError("Invalid Algolia application ID.")
    return app_id


def _index(value: object) -> str:
    index = str(value or "default")
    if not index or len(index) > 256 or "\x00" in index or "\r" in index or "\n" in index:
        raise ValueError("Invalid Algolia index.")
    return quote(index, safe="")


def _object_id(value: object) -> str:
    object_id = str(value or "")
    if not object_id or len(object_id) > 256 or "\x00" in object_id or "/" in object_id:
        raise ValueError("Invalid Algolia object ID.")
    return quote(object_id, safe="")


def _data(value: object) -> dict:
    if not isinstance(value, dict) or not value:
        raise ValueError("Algolia data must be a non-empty object.")
    if len(json.dumps(value, separators=(",", ":"))) > MAX_ALGOLIA_PAYLOAD_BYTES:
        raise ValueError("Algolia data exceeds the allowed size.")
    return value


def _query(value: object) -> str:
    query = str(value or "")
    if len(query) > MAX_ALGOLIA_QUERY_CHARS or "\x00" in query:
        raise ValueError("Invalid Algolia query.")
    return query


def _fmt(response: httpx.Response) -> str:
    response.raise_for_status()
    try:
        return str(response.json())[:2000]
    except ValueError:
        return response.text[:500]


def run(action: str, **kwargs) -> str:
    """Execute bounded Algolia actions with a fixed trusted endpoint suffix."""
    app_id = _app_id(os.getenv("ALGOLIA_APP_ID"))
    api_key = os.getenv("ALGOLIA_API_KEY")
    index = _index(os.getenv("ALGOLIA_INDEX") or kwargs.get("index", "default"))
    if not app_id or not api_key:
        return "Error: Algolia credentials not configured. Set ALGOLIA_APP_ID and ALGOLIA_API_KEY environment variables."

    base_url = f"https://{app_id}-dsn.algolia.net/1/indexes/{index}"
    headers = {"X-Algolia-API-Key": api_key, "X-Algolia-Application-Id": app_id, "Content-Type": "application/json"}

    try:
        if action == "search":
            response = httpx.post(
                base_url,
                headers=headers,
                json={"params": urlencode({"query": _query(kwargs.get("query", "")), "hitsPerPage": MAX_ALGOLIA_HITS})},
                timeout=30,
                follow_redirects=False,
            )
            response.raise_for_status()
            data = response.json()
            return str(data.get("hits", data))[:2000]

        if action == "add_object":
            response = httpx.post(base_url, headers=headers, json=_data(kwargs.get("data", {})), timeout=30, follow_redirects=False)
            return _fmt(response)

        if action == "delete_object":
            response = httpx.delete(f"{base_url}/{_object_id(kwargs.get('id'))}", headers=headers, timeout=30, follow_redirects=False)
            return _fmt(response)

        if action == "search_settings":
            response = httpx.get(f"{base_url}/settings", headers=headers, timeout=30, follow_redirects=False)
            return _fmt(response)

        return "Error: Unknown action. Available: search, add_object, delete_object, search_settings"
    except httpx.TimeoutException:
        return "Error: Request timed out after 30 seconds."
    except (httpx.HTTPError, ValueError) as exc:
        return f"Error: {exc}"
