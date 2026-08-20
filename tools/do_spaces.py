"""Safe DigitalOcean Spaces integration using the S3-compatible boto3 client."""

from __future__ import annotations

import asyncio
import os
import re
from typing import Any
from urllib.parse import quote

import boto3
from botocore.config import Config


_REGION_RE = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?")
_BUCKET_RE = re.compile(r"[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])?")
_MAX_OBJECT_BYTES = 50 * 1024 * 1024


def _region(value: object) -> str:
    region = str(value or "").strip().lower()
    if not _REGION_RE.fullmatch(region):
        raise ValueError("region must be a single canonical DigitalOcean region label.")
    return region


def _bucket_name(value: object) -> str:
    bucket = str(value or "").strip().lower()
    if not _BUCKET_RE.fullmatch(bucket) or ".." in bucket:
        raise ValueError("bucket must be a DNS-compatible Spaces bucket name between 3 and 63 characters.")
    return bucket


def _spaces_key(value: object) -> str:
    key = str(value or "")
    if not key or len(key.encode("utf-8")) > 1024 or any(char in key for char in "\r\n\x00"):
        raise ValueError("key must be non-empty, at most 1,024 bytes, and contain no control characters.")
    segments = key.split("/")
    if any(segment in {"", ".", ".."} for segment in segments):
        raise ValueError("key cannot contain empty, current-directory, or parent-directory path segments.")
    return key


def _spaces_key_path(value: object) -> str:
    """Return an encoded display/path form of a validated object key."""
    return quote(_spaces_key(value), safe="/")


def _client(api_key: str, secret_key: str, region: str):
    access_key = str(api_key or "").strip() or os.getenv("DO_SPACES_ACCESS_KEY")
    secret = str(secret_key or "").strip() or os.getenv("DO_SPACES_SECRET_KEY")
    if not access_key or not secret:
        raise ValueError("DigitalOcean Spaces access key ID and secret access key are required.")
    clean_region = _region(region)
    return boto3.client(
        "s3",
        endpoint_url=f"https://{clean_region}.digitaloceanspaces.com",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret,
        region_name=clean_region,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def _upload_file_sync(api_key: str, secret_key: str, region: str, bucket: str, key: str, body: bytes) -> dict[str, Any]:
    if not isinstance(body, bytes) or len(body) > _MAX_OBJECT_BYTES:
        raise ValueError(f"body must be bytes no larger than {_MAX_OBJECT_BYTES} bytes.")
    clean_bucket = _bucket_name(bucket)
    clean_key = _spaces_key(key)
    _client(api_key, secret_key, region).put_object(Bucket=clean_bucket, Key=clean_key, Body=body)
    return {"status": "uploaded", "bucket": clean_bucket, "key": clean_key, "bytes": len(body)}


def _download_file_sync(api_key: str, secret_key: str, region: str, bucket: str, key: str) -> dict[str, Any]:
    clean_bucket = _bucket_name(bucket)
    clean_key = _spaces_key(key)
    response = _client(api_key, secret_key, region).get_object(Bucket=clean_bucket, Key=clean_key)
    content = response["Body"].read(_MAX_OBJECT_BYTES + 1)
    if len(content) > _MAX_OBJECT_BYTES:
        raise ValueError(f"object exceeds the {_MAX_OBJECT_BYTES}-byte download limit.")
    return {"content": content, "key": clean_key, "bytes": len(content)}


def _list_files_sync(api_key: str, secret_key: str, region: str, bucket: str) -> dict[str, Any]:
    clean_bucket = _bucket_name(bucket)
    response = _client(api_key, secret_key, region).list_objects_v2(Bucket=clean_bucket, MaxKeys=1000)
    return {"keys": [entry.get("Key", "") for entry in response.get("Contents", [])], "bucket": clean_bucket}


def _delete_file_sync(api_key: str, secret_key: str, region: str, bucket: str, key: str) -> dict[str, Any]:
    clean_bucket = _bucket_name(bucket)
    clean_key = _spaces_key(key)
    _client(api_key, secret_key, region).delete_object(Bucket=clean_bucket, Key=clean_key)
    return {"status": "deleted", "bucket": clean_bucket, "key": clean_key}


def _copy_file_sync(api_key: str, secret_key: str, region: str, bucket: str, source: str, dest: str) -> dict[str, Any]:
    clean_bucket = _bucket_name(bucket)
    source_key = _spaces_key(source)
    destination_key = _spaces_key(dest)
    _client(api_key, secret_key, region).copy_object(
        Bucket=clean_bucket,
        Key=destination_key,
        CopySource={"Bucket": clean_bucket, "Key": source_key},
    )
    return {"status": "copied", "bucket": clean_bucket, "source": source_key, "dest": destination_key}


async def upload_file(
    api_key: str,
    region: str,
    bucket: str,
    key: str,
    body: bytes,
    secret_key: str = "",
) -> dict[str, Any]:
    """Upload a bounded object through S3 Signature Version 4."""
    return await asyncio.to_thread(_upload_file_sync, api_key, secret_key, region, bucket, key, body)


async def download_file(api_key: str, region: str, bucket: str, key: str, secret_key: str = "") -> dict[str, Any]:
    """Download a bounded object through signed Spaces authentication."""
    return await asyncio.to_thread(_download_file_sync, api_key, secret_key, region, bucket, key)


async def list_files(api_key: str, region: str, bucket: str, secret_key: str = "") -> dict[str, Any]:
    """List up to 1,000 Space object keys through signed authentication."""
    return await asyncio.to_thread(_list_files_sync, api_key, secret_key, region, bucket)


async def delete_file(api_key: str, region: str, bucket: str, key: str, secret_key: str = "") -> dict[str, Any]:
    """Delete a validated Spaces object through signed authentication."""
    return await asyncio.to_thread(_delete_file_sync, api_key, secret_key, region, bucket, key)


async def copy_file(
    api_key: str,
    region: str,
    bucket: str,
    source: str,
    dest: str,
    secret_key: str = "",
) -> dict[str, Any]:
    """Copy a validated object within one Space through signed authentication."""
    return await asyncio.to_thread(_copy_file_sync, api_key, secret_key, region, bucket, source, dest)
