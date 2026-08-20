"""Safe AWS S3 integration using AWS Signature Version 4 through boto3."""

from __future__ import annotations

import asyncio
import os
import re
from typing import Any
from urllib.parse import quote

import boto3


_BUCKET_RE = re.compile(r"[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])?")
_MAX_OBJECT_BYTES = 50 * 1024 * 1024


def _bucket_name(value: object) -> str:
    """Validate a DNS-compatible S3 bucket name before passing it to the AWS SDK."""
    bucket = str(value or "").strip().lower()
    if not _BUCKET_RE.fullmatch(bucket) or ".." in bucket or bucket.startswith("xn--"):
        raise ValueError("bucket must be a DNS-compatible S3 bucket name between 3 and 63 characters.")
    return bucket


def _s3_key(value: object) -> str:
    """Validate an object key while preserving valid nested prefixes for the S3 SDK."""
    key = str(value or "")
    if not key or len(key.encode("utf-8")) > 1024 or any(char in key for char in "\r\n\x00"):
        raise ValueError("key must be non-empty, at most 1,024 bytes, and contain no control characters.")
    segments = key.split("/")
    if any(segment in {"", ".", ".."} for segment in segments):
        raise ValueError("key cannot contain empty, current-directory, or parent-directory path segments.")
    return key


def _s3_key_path(value: object) -> str:
    """Return the encoded form of a validated object key for logs and route-safe displays."""
    return quote(_s3_key(value), safe="/")


def _credentials(api_key: str, secret_key: str | None = None):
    access_key = str(api_key or "").strip() or os.getenv("AWS_ACCESS_KEY_ID")
    secret = str(secret_key or "").strip() or os.getenv("AWS_SECRET_ACCESS_KEY")
    if not access_key or not secret:
        raise ValueError("AWS access key ID and secret access key are required.")
    return access_key, secret


def _client(api_key: str, secret_key: str | None = None):
    """Create an AWS SDK client that signs requests with Signature Version 4."""
    access_key, secret = _credentials(api_key, secret_key)
    return boto3.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret,
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )


def _create_bucket_sync(name: str, public: bool, api_key: str) -> dict[str, Any]:
    if public:
        raise ValueError("Public S3 buckets are disabled; use an explicit, reviewed distribution workflow instead.")
    bucket = _bucket_name(name)
    client = _client(api_key)
    region = os.getenv("AWS_REGION", "us-east-1")
    args: dict[str, Any] = {"Bucket": bucket}
    if region != "us-east-1":
        args["CreateBucketConfiguration"] = {"LocationConstraint": region}
    client.create_bucket(**args)
    return {"bucket": bucket, "public": False}


def _list_buckets_sync(api_key: str, secret_key: str) -> dict[str, Any]:
    response = _client(api_key, secret_key).list_buckets()
    return {"buckets": [bucket.get("Name", "") for bucket in response.get("Buckets", [])]}


def _upload_object_sync(bucket: str, key: str, body: bytes, api_key: str, secret_key: str) -> dict[str, Any]:
    if not isinstance(body, bytes) or len(body) > _MAX_OBJECT_BYTES:
        raise ValueError(f"body must be bytes no larger than {_MAX_OBJECT_BYTES} bytes.")
    clean_bucket = _bucket_name(bucket)
    clean_key = _s3_key(key)
    _client(api_key, secret_key).put_object(
        Bucket=clean_bucket,
        Key=clean_key,
        Body=body,
        ContentType="application/octet-stream",
    )
    return {"bucket": clean_bucket, "key": clean_key, "bytes": len(body)}


def _download_object_sync(bucket: str, key: str, api_key: str, secret_key: str) -> dict[str, Any]:
    clean_bucket = _bucket_name(bucket)
    clean_key = _s3_key(key)
    response = _client(api_key, secret_key).get_object(Bucket=clean_bucket, Key=clean_key)
    content = response["Body"].read(_MAX_OBJECT_BYTES + 1)
    if len(content) > _MAX_OBJECT_BYTES:
        raise ValueError(f"object exceeds the {_MAX_OBJECT_BYTES}-byte download limit.")
    return {"content": content, "key": clean_key, "bytes": len(content)}


def _delete_object_sync(bucket: str, key: str, api_key: str, secret_key: str) -> dict[str, Any]:
    clean_bucket = _bucket_name(bucket)
    clean_key = _s3_key(key)
    _client(api_key, secret_key).delete_object(Bucket=clean_bucket, Key=clean_key)
    return {"deleted": clean_key, "bucket": clean_bucket}


async def create_bucket(name: str, public: bool, api_key: str) -> dict[str, Any]:
    """Create a private bucket using signed AWS SDK operations."""
    return await asyncio.to_thread(_create_bucket_sync, name, public, api_key)


async def list_buckets(api_key: str, secret_key: str) -> dict[str, Any]:
    """List buckets through a signed AWS SDK client."""
    return await asyncio.to_thread(_list_buckets_sync, api_key, secret_key)


async def upload_object(bucket: str, key: str, body: bytes, api_key: str, secret_key: str) -> dict[str, Any]:
    """Upload a bounded object privately with an AWS SDK-signed request."""
    return await asyncio.to_thread(_upload_object_sync, bucket, key, body, api_key, secret_key)


async def download_object(bucket: str, key: str, api_key: str, secret_key: str) -> dict[str, Any]:
    """Download a bounded object with AWS SDK authentication."""
    return await asyncio.to_thread(_download_object_sync, bucket, key, api_key, secret_key)


async def delete_object(bucket: str, key: str, api_key: str, secret_key: str) -> dict[str, Any]:
    """Delete a validated object through the AWS SDK."""
    return await asyncio.to_thread(_delete_object_sync, bucket, key, api_key, secret_key)
