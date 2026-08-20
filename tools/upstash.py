"""Safe Upstash Redis REST integration."""

from __future__ import annotations

import os
from urllib.parse import quote, urlsplit

import httpx

PLUGIN_NAME = "upstash"
PLUGIN_DESCRIPTION = "Upstash - Redis serverless database"
MAX_UPSTASH_KEY_CHARS = 1024
MAX_UPSTASH_VALUE_CHARS = 65_536
MAX_UPSTASH_TTL_SECONDS = 2_592_000


def _base_url(value: object) -> str:
    raw_url = str(value or "").strip().rstrip("/")
    parsed = urlsplit(raw_url)
    if parsed.scheme != "https" or not parsed.hostname or not parsed.hostname.endswith(".upstash.io"):
        raise ValueError("Upstash REST URL must be an HTTPS upstash.io endpoint.")
    if parsed.username is not None or parsed.password is not None or parsed.query or parsed.fragment:
        raise ValueError("Upstash REST URL must not include credentials, query, or fragment.")
    return raw_url


def _key_path(value: object) -> str:
    key = str(value or "")
    if not key or len(key) > MAX_UPSTASH_KEY_CHARS or "\x00" in key or "\r" in key or "\n" in key:
        raise ValueError("Invalid Upstash key.")
    return quote(key, safe="")


def _value(value: object) -> str:
    text = str(value)
    if len(text) > MAX_UPSTASH_VALUE_CHARS:
        raise ValueError("Upstash value exceeds the allowed size.")
    return text


def _ttl(value: object) -> int:
    try:
        ttl = int(value)
    except (TypeError, ValueError):
        raise ValueError("Upstash TTL must be an integer.") from None
    if ttl < 1 or ttl > MAX_UPSTASH_TTL_SECONDS:
        raise ValueError(f"Upstash TTL must be between 1 and {MAX_UPSTASH_TTL_SECONDS} seconds.")
    return ttl


def _fmt(response: httpx.Response) -> str:
    response.raise_for_status()
    try:
        return str(response.json())[:2000]
    except ValueError:
        return response.text[:500]


def run(action: str, **kwargs) -> str:
    """Execute bounded Upstash Redis REST operations."""
    url = os.getenv("UPSTASH_REDIS_REST_URL")
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    if not url or not token:
        return "Error: Upstash credentials not configured. Set UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN environment variables."

    try:
        base_url = _base_url(url)
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        if action == "get":
            response = httpx.get(f"{base_url}/get/{_key_path(kwargs.get('key'))}", headers=headers, timeout=30, follow_redirects=False)
            return _fmt(response)

        if action == "set":
            path = f"{base_url}/set/{_key_path(kwargs.get('key'))}"
            ttl_value = kwargs.get("ttl", 0)
            if ttl_value:
                path += f"/ex/{_ttl(ttl_value)}"
            response = httpx.post(path, headers=headers, json=_value(kwargs.get("value")), timeout=30, follow_redirects=False)
            return _fmt(response)

        if action == "incr":
            response = httpx.post(f"{base_url}/incr/{_key_path(kwargs.get('key'))}", headers=headers, timeout=30, follow_redirects=False)
            return _fmt(response)

        if action == "del":
            response = httpx.post(f"{base_url}/del/{_key_path(kwargs.get('key'))}", headers=headers, timeout=30, follow_redirects=False)
            return _fmt(response)

        if action == "ping":
            response = httpx.get(f"{base_url}/ping", headers=headers, timeout=30, follow_redirects=False)
            return _fmt(response)

        return "Error: Unknown action. Available: get, set, incr, del, ping"
    except httpx.TimeoutException:
        return "Error: Request timed out after 30 seconds."
    except (httpx.HTTPError, ValueError) as exc:
        return f"Error: {exc}"
