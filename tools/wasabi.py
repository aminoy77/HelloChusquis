"""Safe Wasabi integration using the S3-compatible boto3 client."""

from __future__ import annotations

import asyncio
import os
import re
from typing import Any
from urllib.parse import quote

import boto3
from botocore.config import Config


_ENDPOINT = "https://s3.wasabisys.com"
_BUCKET_RE = re.compile(r"[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])?")
_MAX_OBJECT_BYTES = 50 * 1024 * 1024


def _bucket_name(value: object) -> str:
    bucket = str(value or "").strip().lower()
    if not _BUCKET_RE.fullmatch(bucket) or ".." in bucket:
        raise ValueError("bucket must be a DNS-compatible Wasabi bucket name between 3 and 63 characters.")
    return bucket


def _wasabi_key(value: object, field_name: str = "file_path") -> str:
    key = str(value or "")
    if not key or len(key.encode("utf-8")) > 1024 or any(char in key for char in "\r\n\x00"):
        raise ValueError(f"{field_name} must be non-empty, at most 1,024 bytes, and contain no control characters.")
    segments = key.split("/")
    if any(segment in {"", ".", ".."} for segment in segments):
        raise ValueError(f"{field_name} cannot contain empty, current-directory, or parent-directory path segments.")
    return key


def _wasabi_key_path(value: object) -> str:
    """Return an encoded display/path form of a validated object key."""
    return quote(_wasabi_key(value), safe="/")


def _prefix(value: object) -> str:
    prefix = str(value or "")
    if not prefix:
        return ""
    return _wasabi_key(prefix, "prefix")


def _client(api_key: str, secret_key: str):
    access_key = str(api_key or "").strip() or os.getenv("WASABI_ACCESS_KEY")
    secret = str(secret_key or "").strip() or os.getenv("WASABI_SECRET_KEY")
    if not access_key or not secret:
        raise ValueError("Wasabi access key ID and secret access key are required.")
    return boto3.client(
        "s3",
        endpoint_url=_ENDPOINT,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret,
        region_name=os.getenv("WASABI_REGION", "us-east-1"),
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def _upload_file_sync(api_key: str, secret_key: str, bucket: str, file_path: str, content: bytes) -> dict[str, Any]:
    if not isinstance(content, bytes) or len(content) > _MAX_OBJECT_BYTES:
        raise ValueError(f"content must be bytes no larger than {_MAX_OBJECT_BYTES} bytes.")
    clean_bucket = _bucket_name(bucket)
    clean_key = _wasabi_key(file_path)
    _client(api_key, secret_key).put_object(Bucket=clean_bucket, Key=clean_key, Body=content)
    return {"status": "uploaded", "bucket": clean_bucket, "path": clean_key, "bytes": len(content)}


def _download_file_sync(api_key: str, secret_key: str, bucket: str, file_path: str) -> dict[str, Any]:
    clean_bucket = _bucket_name(bucket)
    clean_key = _wasabi_key(file_path)
    response = _client(api_key, secret_key).get_object(Bucket=clean_bucket, Key=clean_key)
    content = response["Body"].read(_MAX_OBJECT_BYTES + 1)
    if len(content) > _MAX_OBJECT_BYTES:
        raise ValueError(f"object exceeds the {_MAX_OBJECT_BYTES}-byte download limit.")
    return {"content": content, "path": clean_key, "bytes": len(content)}


def _list_files_sync(api_key: str, secret_key: str, bucket: str, prefix: str) -> dict[str, Any]:
    clean_bucket = _bucket_name(bucket)
    response = _client(api_key, secret_key).list_objects_v2(
        Bucket=clean_bucket,
        Prefix=_prefix(prefix),
        MaxKeys=1000,
    )
    return {"keys": [entry.get("Key", "") for entry in response.get("Contents", [])], "bucket": clean_bucket}


def _delete_file_sync(api_key: str, secret_key: str, bucket: str, file_path: str) -> dict[str, Any]:
    clean_bucket = _bucket_name(bucket)
    clean_key = _wasabi_key(file_path)
    _client(api_key, secret_key).delete_object(Bucket=clean_bucket, Key=clean_key)
    return {"status": "deleted", "bucket": clean_bucket, "path": clean_key}


def _copy_file_sync(api_key: str, secret_key: str, bucket: str, source: str, destination: str) -> dict[str, Any]:
    clean_bucket = _bucket_name(bucket)
    source_key = _wasabi_key(source, "source")
    destination_key = _wasabi_key(destination, "destination")
    _client(api_key, secret_key).copy_object(
        Bucket=clean_bucket,
        Key=destination_key,
        CopySource={"Bucket": clean_bucket, "Key": source_key},
    )
    return {"status": "copied", "bucket": clean_bucket, "source": source_key, "destination": destination_key}


async def upload_file(api_key: str, bucket: str, file_path: str, content: bytes, secret_key: str = "") -> dict[str, Any]:
    """Upload a bounded Wasabi object through S3 Signature Version 4."""
    return await asyncio.to_thread(_upload_file_sync, api_key, secret_key, bucket, file_path, content)


async def download_file(api_key: str, bucket: str, file_path: str, secret_key: str = "") -> dict[str, Any]:
    """Download a bounded Wasabi object through signed authentication."""
    return await asyncio.to_thread(_download_file_sync, api_key, secret_key, bucket, file_path)


async def list_files(api_key: str, bucket: str, prefix: str = "", secret_key: str = "") -> dict[str, Any]:
    """List up to 1,000 Wasabi keys through signed authentication."""
    return await asyncio.to_thread(_list_files_sync, api_key, secret_key, bucket, prefix)


async def delete_file(api_key: str, bucket: str, file_path: str, secret_key: str = "") -> dict[str, Any]:
    """Delete a validated Wasabi object through signed authentication."""
    return await asyncio.to_thread(_delete_file_sync, api_key, secret_key, bucket, file_path)


async def copy_file(
    api_key: str,
    bucket: str,
    source: str,
    destination: str,
    secret_key: str = "",
) -> dict[str, Any]:
    """Copy a validated object within one Wasabi bucket through signed authentication."""
    return await asyncio.to_thread(_copy_file_sync, api_key, secret_key, bucket, source, destination)
