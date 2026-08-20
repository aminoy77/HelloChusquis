"""Safe Cloudflare R2 integration using the S3-compatible boto3 client."""

from __future__ import annotations

import asyncio
import re
from typing import Any
from urllib.parse import quote

import boto3
from botocore.config import Config


_ACCOUNT_ID_RE = re.compile(r"[a-f0-9]{32}")
_BUCKET_RE = re.compile(r"[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])?")
_MAX_OBJECT_BYTES = 50 * 1024 * 1024


def _account_id(value: object) -> str:
    account_id = str(value or "").strip().lower()
    if not _ACCOUNT_ID_RE.fullmatch(account_id):
        raise ValueError("account_id must be a 32-character hexadecimal Cloudflare account ID.")
    return account_id


def _bucket_name(value: object) -> str:
    bucket = str(value or "").strip().lower()
    if not _BUCKET_RE.fullmatch(bucket) or ".." in bucket:
        raise ValueError("bucket must be a DNS-compatible R2 bucket name between 3 and 63 characters.")
    return bucket


def _r2_key(value: object) -> str:
    key = str(value or "")
    if not key or len(key.encode("utf-8")) > 1024 or any(char in key for char in "\r\n\x00"):
        raise ValueError("key must be non-empty, at most 1,024 bytes, and contain no control characters.")
    segments = key.split("/")
    if any(segment in {"", ".", ".."} for segment in segments):
        raise ValueError("key cannot contain empty, current-directory, or parent-directory path segments.")
    return key


def _r2_key_path(value: object) -> str:
    """Return an encoded display/path form of a validated R2 object key."""
    return quote(_r2_key(value), safe="/")


def _expires(value: object) -> int:
    try:
        expires = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("expires must be an integer between 60 and 3,600 seconds.") from exc
    if not 60 <= expires <= 3600:
        raise ValueError("expires must be between 60 and 3,600 seconds.")
    return expires


def _client(account_id: str, access_key: str, secret_key: str):
    clean_account_id = _account_id(account_id)
    if not access_key or not secret_key:
        raise ValueError("R2 access key ID and secret access key are required.")
    return boto3.client(
        "s3",
        endpoint_url=f"https://{clean_account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def _upload_file_sync(account_id: str, access_key: str, secret_key: str, bucket: str, key: str, body: bytes) -> dict[str, Any]:
    if not isinstance(body, bytes) or len(body) > _MAX_OBJECT_BYTES:
        raise ValueError(f"body must be bytes no larger than {_MAX_OBJECT_BYTES} bytes.")
    clean_bucket = _bucket_name(bucket)
    clean_key = _r2_key(key)
    _client(account_id, access_key, secret_key).put_object(Bucket=clean_bucket, Key=clean_key, Body=body)
    return {"status": "uploaded", "bucket": clean_bucket, "key": clean_key, "bytes": len(body)}


def _download_file_sync(account_id: str, access_key: str, secret_key: str, bucket: str, key: str) -> dict[str, Any]:
    clean_bucket = _bucket_name(bucket)
    clean_key = _r2_key(key)
    response = _client(account_id, access_key, secret_key).get_object(Bucket=clean_bucket, Key=clean_key)
    content = response["Body"].read(_MAX_OBJECT_BYTES + 1)
    if len(content) > _MAX_OBJECT_BYTES:
        raise ValueError(f"object exceeds the {_MAX_OBJECT_BYTES}-byte download limit.")
    return {"content": content, "key": clean_key, "bytes": len(content)}


def _list_files_sync(account_id: str, access_key: str, secret_key: str, bucket: str) -> dict[str, Any]:
    clean_bucket = _bucket_name(bucket)
    response = _client(account_id, access_key, secret_key).list_objects_v2(Bucket=clean_bucket, MaxKeys=1000)
    return {"keys": [entry.get("Key", "") for entry in response.get("Contents", [])], "bucket": clean_bucket}


def _delete_file_sync(account_id: str, access_key: str, secret_key: str, bucket: str, key: str) -> dict[str, Any]:
    clean_bucket = _bucket_name(bucket)
    clean_key = _r2_key(key)
    _client(account_id, access_key, secret_key).delete_object(Bucket=clean_bucket, Key=clean_key)
    return {"status": "deleted", "bucket": clean_bucket, "key": clean_key}


def _signed_url_sync(account_id: str, access_key: str, secret_key: str, bucket: str, key: str, expires: int) -> dict[str, str]:
    clean_bucket = _bucket_name(bucket)
    clean_key = _r2_key(key)
    url = _client(account_id, access_key, secret_key).generate_presigned_url(
        "get_object",
        Params={"Bucket": clean_bucket, "Key": clean_key},
        ExpiresIn=_expires(expires),
    )
    return {"url": url}


async def upload_file(account_id: str, access_key: str, secret_key: str, bucket: str, key: str, body: bytes) -> dict[str, Any]:
    """Upload a bounded R2 object through AWS Signature Version 4."""
    return await asyncio.to_thread(_upload_file_sync, account_id, access_key, secret_key, bucket, key, body)


async def download_file(account_id: str, access_key: str, secret_key: str, bucket: str, key: str) -> dict[str, Any]:
    """Download a bounded R2 object through the signed S3-compatible client."""
    return await asyncio.to_thread(_download_file_sync, account_id, access_key, secret_key, bucket, key)


async def list_files(account_id: str, access_key: str, secret_key: str, bucket: str) -> dict[str, Any]:
    """List up to 1,000 R2 object keys through the signed client."""
    return await asyncio.to_thread(_list_files_sync, account_id, access_key, secret_key, bucket)


async def delete_file(account_id: str, access_key: str, secret_key: str, bucket: str, key: str) -> dict[str, Any]:
    """Delete a validated R2 object through AWS Signature Version 4."""
    return await asyncio.to_thread(_delete_file_sync, account_id, access_key, secret_key, bucket, key)


async def get_signed_url(
    account_id: str,
    access_key: str,
    secret_key: str,
    bucket: str,
    key: str,
    expires: int = 3600,
) -> dict[str, str]:
    """Generate a bounded-expiry S3v4 presigned download URL for one validated object."""
    return await asyncio.to_thread(_signed_url_sync, account_id, access_key, secret_key, bucket, key, expires)
