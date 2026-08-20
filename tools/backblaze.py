"""Safe Backblaze B2 integration for authenticated file metadata operations."""

from __future__ import annotations

import re
from typing import Any

from httpx import AsyncClient


_B2_API_URL = "https://api.backblazeb2.com/b2api/v2"
_TOKEN_RE = re.compile(r"[A-Za-z0-9_-]{1,512}")
_BUCKET_NAME_RE = re.compile(r"[a-z0-9][a-z0-9-]{4,62}")
_MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024


def _file_id(value: object) -> str:
    """Validate a Backblaze file identifier before it is used as a request value."""
    file_id = str(value or "").strip()
    if not _TOKEN_RE.fullmatch(file_id):
        raise ValueError("file_id must be a single safe Backblaze token.")
    return file_id


def _bucket_id(value: object) -> str:
    bucket_id = str(value or "").strip()
    if not _TOKEN_RE.fullmatch(bucket_id):
        raise ValueError("bucket_id must be a single safe Backblaze token.")
    return bucket_id


def _bucket_name(value: object) -> str:
    name = str(value or "").strip().lower()
    if not _BUCKET_NAME_RE.fullmatch(name):
        raise ValueError("bucket name must be lowercase, 6 to 63 characters, and use only letters, numbers, and hyphens.")
    return name


def _file_name(value: object) -> str:
    name = str(value or "")
    if not name or len(name.encode("utf-8")) > 1024 or any(char in name for char in "\r\n\x00"):
        raise ValueError("file_name must be non-empty, at most 1,024 bytes, and contain no control characters.")
    if any(segment in {"", ".", ".."} for segment in name.split("/")):
        raise ValueError("file_name cannot contain empty, current-directory, or parent-directory segments.")
    return name


def _bucket_type(value: object) -> str:
    bucket_type = str(value or "allPrivate").strip()
    if bucket_type != "allPrivate":
        raise ValueError("Only private Backblaze buckets are permitted by this integration.")
    return bucket_type


def _headers(api_key: str) -> dict[str, str]:
    token = str(api_key or "").strip()
    if not token or any(char in token for char in "\r\n\x00"):
        raise ValueError("A valid Backblaze authorization token is required.")
    return {"Authorization": token}


async def _request(
    method: str,
    path: str,
    api_key: str,
    *,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    expect_json: bool = True,
) -> dict[str, Any]:
    """Perform one bounded B2 request without following redirects."""
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.request(
            method,
            f"{_B2_API_URL}{path}",
            json=json,
            params=params,
            headers=_headers(api_key),
        )
        if expect_json:
            return response.json()
        content = await response.aread()
        if len(content) > _MAX_DOWNLOAD_BYTES:
            raise ValueError(f"file exceeds the {_MAX_DOWNLOAD_BYTES}-byte download limit.")
        return {"content": content, "status": response.status_code}


async def upload_file(api_key: str, path: str) -> dict[str, Any]:
    """Reject the incomplete legacy upload API rather than pretending a local path was uploaded."""
    del api_key, path
    raise ValueError(
        "Backblaze uploads require an authorized upload URL, bucket ID, file name, and file bytes; "
        "the legacy upload_file signature cannot safely perform that operation."
    )


async def download_file(api_key: str, file_id: str) -> dict[str, Any]:
    """Download a bounded file by validated Backblaze file identifier."""
    return await _request(
        "GET",
        "/b2_download_file_by_id",
        api_key,
        params={"fileId": _file_id(file_id)},
        expect_json=False,
    )


async def list_files(api_key: str, bucket_id: str) -> dict[str, Any]:
    """List file versions from a validated bucket through structured JSON input."""
    return await _request(
        "POST",
        "/b2_list_file_versions",
        api_key,
        json={"bucketId": _bucket_id(bucket_id), "maxFileCount": 1000},
    )


async def create_bucket(api_key: str, name: str, type: str = "allPrivate") -> dict[str, Any]:
    """Create a private Backblaze bucket with validated name and type."""
    return await _request(
        "POST",
        "/b2_create_bucket",
        api_key,
        json={"bucketName": _bucket_name(name), "bucketType": _bucket_type(type)},
    )


async def delete_file(api_key: str, file_id: str, file_name: str = "") -> dict[str, Any]:
    """Delete a file version only when both required validated B2 identifiers are supplied."""
    return await _request(
        "POST",
        "/b2_delete_file_version",
        api_key,
        json={"fileId": _file_id(file_id), "fileName": _file_name(file_name)},
    )
