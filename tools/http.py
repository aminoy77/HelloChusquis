"""Safe generic HTTP client for approved external requests."""

from __future__ import annotations

import json as json_lib
from typing import Any

from httpx import AsyncClient

from tools.web_fetch import validate_url_safety


_MAX_URL_CHARS = 8192
_MAX_RESPONSE_BYTES = 256 * 1024


def _safe_url(value: object) -> str:
    """Validate an external URL through the shared SSRF policy before connecting."""
    url = str(value or "").strip()
    if not url or len(url) > _MAX_URL_CHARS or any(char in url for char in "\r\n\x00"):
        raise ValueError("url must be non-empty, within 8,192 characters, and contain no control characters.")
    return validate_url_safety(url)


def _safe_headers(headers: dict[str, Any] | None) -> dict[str, str]:
    """Reject malformed header names and values before passing them to the HTTP stack."""
    if headers is None:
        return {}
    if not isinstance(headers, dict) or len(headers) > 100:
        raise ValueError("headers must be a dictionary with at most 100 entries.")
    clean_headers: dict[str, str] = {}
    for key, value in headers.items():
        name = str(key)
        text = str(value)
        if not name or any(char in name or char in text for char in "\r\n\x00"):
            raise ValueError("headers cannot contain empty names or control characters.")
        clean_headers[name] = text
    return clean_headers


async def _response_payload(response) -> Any:
    """Read a response up to a fixed byte budget and parse JSON when complete."""
    content = bytearray()
    truncated = False
    async for chunk in response.aiter_bytes():
        remaining = _MAX_RESPONSE_BYTES - len(content)
        if remaining <= 0:
            truncated = True
            break
        content.extend(chunk[:remaining])
        if len(chunk) > remaining:
            truncated = True
            break

    text = content.decode(response.encoding or "utf-8", errors="replace")
    if truncated:
        return {"text": text, "truncated": True, "status": response.status_code}
    try:
        return json_lib.loads(text) if text else {"status": response.status_code}
    except json_lib.JSONDecodeError:
        return {"text": text, "status": response.status_code}


async def _request(
    method: str,
    url: str,
    *,
    json: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
    headers: dict[str, Any] | None = None,
) -> Any:
    """Issue one externally approved request with SSRF and response-size controls."""
    safe_url = _safe_url(url)
    safe_headers = _safe_headers(headers)
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        async with client.stream(
            method,
            safe_url,
            json=json,
            data=data,
            headers=safe_headers,
        ) as response:
            return await _response_payload(response)


async def get(url: str, headers: dict[str, Any] | None = None) -> Any:
    """Perform a generic SSRF-safe GET request."""
    return await _request("GET", url, headers=headers)


async def post(
    url: str,
    json: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
    headers: dict[str, Any] | None = None,
) -> Any:
    """Perform a generic SSRF-safe POST request."""
    return await _request("POST", url, json=json, data=data, headers=headers)


async def put(
    url: str,
    json: dict[str, Any] | None = None,
    headers: dict[str, Any] | None = None,
) -> Any:
    """Perform a generic SSRF-safe PUT request."""
    return await _request("PUT", url, json=json, headers=headers)


async def delete(url: str, headers: dict[str, Any] | None = None) -> dict[str, int]:
    """Perform a generic SSRF-safe DELETE request and return its status code."""
    payload = await _request("DELETE", url, headers=headers)
    if isinstance(payload, dict) and isinstance(payload.get("status"), int):
        return {"status": payload["status"]}
    return {"status": 200}


async def patch(
    url: str,
    json: dict[str, Any] | None = None,
    headers: dict[str, Any] | None = None,
) -> Any:
    """Perform a generic SSRF-safe PATCH request."""
    return await _request("PATCH", url, json=json, headers=headers)
