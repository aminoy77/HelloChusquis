"""Safe Box Content API integration."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx


_API_BASE_URL = "https://api.box.com/2.0"
_UPLOAD_BASE_URL = "https://upload.box.com/api/2.0"
_ID_RE = re.compile(r"[0-9]{1,19}")
_MAX_UPLOAD_BYTES = 50 * 1024 * 1024
_SHARED_LINK_ACCESS = frozenset({"company", "collaborators", "open"})


def _box_id(value: object, field_name: str) -> str:
    """Validate a Box numeric resource ID before embedding it in an API path."""
    identifier = str(value or "").strip()
    if not _ID_RE.fullmatch(identifier):
        raise ValueError(f"{field_name} must be a positive numeric Box identifier.")
    return identifier


def _name(value: object, field_name: str) -> str:
    name = str(value or "").strip()
    if not name or len(name) > 255 or any(char in name for char in "\r\n\x00"):
        raise ValueError(f"{field_name} must be non-empty, at most 255 characters, and contain no control characters.")
    return name


def _headers(api_key: str) -> dict[str, str]:
    token = str(api_key or "").strip()
    if not token or any(char in token for char in "\r\n\x00"):
        raise ValueError("A valid Box access token is required.")
    return {"Authorization": f"Bearer {token}"}


def _shared_access(value: object) -> str:
    access = str(value or "company").strip()
    if access not in _SHARED_LINK_ACCESS:
        raise ValueError("access must be one of: company, collaborators, open.")
    return access


async def _request(
    method: str,
    url: str,
    api_key: str,
    *,
    json_body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    files: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Perform one bounded Box API request without following redirects."""
    async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.request(
            method,
            url,
            headers=_headers(api_key),
            json=json_body,
            params=params,
            files=files,
        )
        return response.json()


async def upload_file(api_key: str, file_id: str, content: bytes, name: str) -> dict[str, Any]:
    """Upload a bounded new version for a validated existing Box file."""
    if not isinstance(content, bytes) or len(content) > _MAX_UPLOAD_BYTES:
        raise ValueError(f"content must be bytes no larger than {_MAX_UPLOAD_BYTES} bytes.")
    clean_file_id = _box_id(file_id, "file_id")
    clean_name = _name(name, "name")
    return await _request(
        "POST",
        f"{_UPLOAD_BASE_URL}/files/{clean_file_id}/content",
        api_key,
        files={
            "attributes": (None, json.dumps({"name": clean_name}), "application/json"),
            "file": (clean_name, content, "application/octet-stream"),
        },
    )


async def get_file(api_key: str, file_id: str) -> dict[str, Any]:
    """Get metadata for a validated Box file."""
    return await _request("GET", f"{_API_BASE_URL}/files/{_box_id(file_id, 'file_id')}", api_key)


async def list_folder(api_key: str, folder_id: str = "0", limit: int = 1000) -> dict[str, Any]:
    """List a bounded page of items in a validated Box folder."""
    try:
        page_size = int(limit)
    except (TypeError, ValueError) as exc:
        raise ValueError("limit must be an integer between 1 and 1,000.") from exc
    if not 1 <= page_size <= 1000:
        raise ValueError("limit must be between 1 and 1,000.")
    return await _request(
        "GET",
        f"{_API_BASE_URL}/folders/{_box_id(folder_id, 'folder_id')}/items",
        api_key,
        params={"limit": page_size},
    )


async def create_folder(api_key: str, name: str, parent_id: str = "0") -> dict[str, Any]:
    """Create a folder with a validated name in a validated parent folder."""
    return await _request(
        "POST",
        f"{_API_BASE_URL}/folders",
        api_key,
        json_body={"name": _name(name, "name"), "parent": {"id": _box_id(parent_id, "parent_id")}},
    )


async def share_file(api_key: str, file_id: str, access: str = "company") -> dict[str, Any]:
    """Create a shared link with an internal-only default; public access must be explicit."""
    return await _request(
        "PUT",
        f"{_API_BASE_URL}/files/{_box_id(file_id, 'file_id')}",
        api_key,
        json_body={"shared_link": {"access": _shared_access(access)}},
    )
