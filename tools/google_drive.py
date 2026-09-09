"""Safe Google Drive API integration."""

from __future__ import annotations

import json
import re
from typing import Any

from httpx import AsyncClient


_DRIVE_FILES_URL = "https://www.googleapis.com/drive/v3/files"
_DRIVE_UPLOAD_URL = "https://www.googleapis.com/upload/drive/v3/files"
_DRIVE_ID_RE = re.compile(r"[A-Za-z0-9_-]{1,256}")
_EMAIL_RE = re.compile(
    r"[A-Za-z0-9.!#$%&'*+=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+"
)
_MAX_UPLOAD_BYTES = 50 * 1024 * 1024


def _drive_id(value: object) -> str:
    """Validate a Drive resource identifier before using it as a path component."""
    identifier = str(value or "").strip()
    if not _DRIVE_ID_RE.fullmatch(identifier):
        raise ValueError("Google Drive identifier must be a single safe path segment.")
    return identifier


def _folder_id(value: object) -> str:
    folder_id = str(value or "root").strip()
    return "root" if folder_id == "root" else _drive_id(folder_id)


def _bounded_page_size(value: object, default: int = 100) -> int:
    try:
        page_size = int(value)
    except (TypeError, ValueError):
        page_size = default
    return max(1, min(page_size, 1000))


def _file_name(value: object) -> str:
    name = str(value or "").strip()
    if not name or len(name) > 255 or any(char in name for char in "\r\n\x00"):
        raise ValueError("File name must be non-empty and cannot contain control characters.")
    return name


def _email(value: object) -> str:
    email = str(value or "").strip()
    if len(email) > 254 or not _EMAIL_RE.fullmatch(email):
        raise ValueError("A valid email address is required.")
    return email


def _headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


async def _request(
    method: str,
    url: str,
    access_token: str,
    *,
    json_data: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    expect_json: bool = True,
) -> dict[str, Any]:
    """Perform one redirect-free, timeout-bounded Drive request."""
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.request(
            method,
            url,
            json=json_data,
            params=params,
            headers=_headers(access_token),
        )
        if expect_json:
            return response.json()
        return {"content": response.content, "content_type": response.headers.get("content-type", "")}


async def list_files(
    access_token: str,
    folder_id: str = "root",
    page_size: int = 100,
) -> dict[str, Any]:
    """List a bounded page of files in the requested, validated folder."""
    parent = _folder_id(folder_id)
    return await _request(
        "GET",
        _DRIVE_FILES_URL,
        access_token,
        params={
            "q": f"'{parent}' in parents and trashed = false",
            "pageSize": _bounded_page_size(page_size),
        },
    )


async def upload_file(
    access_token: str,
    name: str,
    content: bytes,
    mime_type: str = "text/plain",
) -> dict[str, Any]:
    """Upload a named file through Drive's multipart upload endpoint."""
    if not isinstance(content, bytes) or len(content) > _MAX_UPLOAD_BYTES:
        raise ValueError(f"content must be bytes no larger than {_MAX_UPLOAD_BYTES} bytes.")
    clean_name = _file_name(name)
    clean_mime_type = str(mime_type or "application/octet-stream").strip()[:255]
    if not clean_mime_type or any(char in clean_mime_type for char in "\r\n"):
        raise ValueError("mime_type must not contain control characters.")
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.post(
            _DRIVE_UPLOAD_URL,
            params={"uploadType": "multipart"},
            files={
                "metadata": (None, json.dumps({"name": clean_name}), "application/json"),
                "file": (clean_name, content, clean_mime_type),
            },
            headers=_headers(access_token),
        )
        return response.json()


async def download_file(access_token: str, file_id: str) -> dict[str, Any]:
    """Download file bytes rather than returning metadata from the file endpoint."""
    return await _request(
        "GET",
        f"{_DRIVE_FILES_URL}/{_drive_id(file_id)}",
        access_token,
        params={"alt": "media"},
        expect_json=False,
    )


async def create_folder(access_token: str, name: str, parent_id: str | None = None) -> dict[str, Any]:
    """Create a Drive folder, optionally beneath a validated parent identifier."""
    metadata: dict[str, Any] = {
        "name": _file_name(name),
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        metadata["parents"] = [_folder_id(parent_id)]
    return await _request("POST", _DRIVE_FILES_URL, access_token, json_data=metadata)


async def share_file(access_token: str, file_id: str, email: str) -> dict[str, Any]:
    """Grant read access to a file selected by a validated resource identifier."""
    return await _request(
        "POST",
        f"{_DRIVE_FILES_URL}/{_drive_id(file_id)}/permissions",
        access_token,
        json_data={"type": "user", "role": "reader", "emailAddress": _email(email)},
    )


async def search_files(access_token: str, query: str, page_size: int = 100) -> dict[str, Any]:
    """Search Drive with a bounded structured query parameter."""
    return await _request(
        "GET",
        _DRIVE_FILES_URL,
        access_token,
        params={"q": str(query or "")[:4096], "pageSize": _bounded_page_size(page_size)},
    )
