"""Safe Dropbox API integration."""

from __future__ import annotations

import json
from typing import Any

import httpx


_API_BASE_URL = "https://api.dropboxapi.com/2"
_CONTENT_BASE_URL = "https://content.dropboxapi.com/2"
_MAX_TRANSFER_BYTES = 50 * 1024 * 1024
_SHARED_AUDIENCES = frozenset({"team", "public", "no_one"})


def _dropbox_path(value: object) -> str:
    """Validate a non-root Dropbox file or folder path."""
    path = str(value or "")
    if not path.startswith("/") or path == "/" or len(path.encode("utf-8")) > 4096:
        raise ValueError("path must be a non-root Dropbox path beginning with '/'.")
    if any(char in path for char in "\r\n\x00") or any(segment in {"", ".", ".."} for segment in path.split("/")[1:]):
        raise ValueError("path cannot contain empty, current-directory, parent-directory, or control-character segments.")
    return path


def _folder_path(value: object) -> str:
    """Validate a Dropbox folder path while permitting the empty root path for listing."""
    path = str(value or "")
    return "" if not path else _dropbox_path(path)


def _headers(access_token: str) -> dict[str, str]:
    token = str(access_token or "").strip()
    if not token or any(char in token for char in "\r\n\x00"):
        raise ValueError("A valid Dropbox access token is required.")
    return {"Authorization": f"Bearer {token}"}


def _audience(value: object) -> str:
    audience = str(value or "team").strip()
    if audience not in _SHARED_AUDIENCES:
        raise ValueError("audience must be one of: team, public, no_one.")
    return audience


async def _json_request(
    method: str,
    url: str,
    access_token: str,
    *,
    json_body: dict[str, Any] | None = None,
    content: bytes | None = None,
    extra_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Perform a Dropbox JSON request with fixed timeout and redirect policy."""
    headers = _headers(access_token)
    if extra_headers:
        headers.update(extra_headers)
    async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.request(method, url, json=json_body, content=content, headers=headers)
        return response.json()


async def upload_file(access_token: str, path: str, content: bytes) -> dict[str, Any]:
    """Upload a bounded file to a validated Dropbox path."""
    if not isinstance(content, bytes) or len(content) > _MAX_TRANSFER_BYTES:
        raise ValueError(f"content must be bytes no larger than {_MAX_TRANSFER_BYTES} bytes.")
    clean_path = _dropbox_path(path)
    return await _json_request(
        "POST",
        f"{_CONTENT_BASE_URL}/files/upload",
        access_token,
        content=content,
        extra_headers={
            "Content-Type": "application/octet-stream",
            "Dropbox-API-Arg": json.dumps({"path": clean_path, "mode": "add", "autorename": True}),
        },
    )


async def download_file(access_token: str, path: str) -> dict[str, Any]:
    """Download a bounded file from a validated Dropbox path."""
    clean_path = _dropbox_path(path)
    headers = _headers(access_token)
    headers["Dropbox-API-Arg"] = json.dumps({"path": clean_path})
    content = bytearray()
    async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
        async with client.stream("POST", f"{_CONTENT_BASE_URL}/files/download", headers=headers) as response:
            async for chunk in response.aiter_bytes():
                remaining = _MAX_TRANSFER_BYTES - len(content)
                if remaining <= 0 or len(chunk) > remaining:
                    raise ValueError(f"file exceeds the {_MAX_TRANSFER_BYTES}-byte download limit.")
                content.extend(chunk)
    return {"content": bytes(content), "path": clean_path, "bytes": len(content)}


async def list_files(access_token: str, path: str = "", limit: int = 1000) -> dict[str, Any]:
    """List a bounded page of entries in a validated Dropbox folder."""
    try:
        page_size = int(limit)
    except (TypeError, ValueError) as exc:
        raise ValueError("limit must be an integer between 1 and 2,000.") from exc
    if not 1 <= page_size <= 2000:
        raise ValueError("limit must be between 1 and 2,000.")
    return await _json_request(
        "POST",
        f"{_API_BASE_URL}/files/list_folder",
        access_token,
        json_body={"path": _folder_path(path), "limit": page_size},
    )


async def create_folder(access_token: str, path: str) -> dict[str, Any]:
    """Create a validated Dropbox folder without automatic rename surprises."""
    return await _json_request(
        "POST",
        f"{_API_BASE_URL}/files/create_folder_v2",
        access_token,
        json_body={"path": _dropbox_path(path), "autorename": False},
    )


async def delete_file(access_token: str, path: str) -> dict[str, Any]:
    """Delete a validated Dropbox path."""
    return await _json_request(
        "POST",
        f"{_API_BASE_URL}/files/delete_v2",
        access_token,
        json_body={"path": _dropbox_path(path)},
    )


async def get_shared_link(access_token: str, path: str, audience: str = "team") -> dict[str, Any]:
    """Create a shared link with internal-team visibility by default; public links require an explicit audience."""
    return await _json_request(
        "POST",
        f"{_API_BASE_URL}/sharing/create_shared_link_with_settings",
        access_token,
        json_body={"path": _dropbox_path(path), "settings": {"audience": _audience(audience)}},
    )
