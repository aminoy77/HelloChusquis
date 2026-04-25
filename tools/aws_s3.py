from httpx import AsyncClient
import json


async def create_bucket(name: str, public: bool, api_key: str) -> dict:
    """Create AWS S3 bucket."""
    url = "https://s3.amazonaws.com/{bucket-name}"
    async with AsyncClient() as client:
        r = await client.put(url, json={"Bucket": name, "ACL": "public-read" if public else "private"},
            headers={"x-amz-api-key": api_key})
        return {"bucket": name, "public": public}


async def list_buckets(api_key: str, secret_key: str) -> dict:
    """List S3 buckets."""
    url = "https://s3.amazonaws.com/"
    async with AsyncClient() as client:
        r = await client.get(url, auth=(api_key, secret_key))
        return r.json()


async def upload_object(bucket: str, key: str, body: bytes, api_key: str, secret_key: str) -> dict:
    """Upload to S3."""
    url = f"https://{bucket}.s3.amazonaws.com/{key}"
    async with AsyncClient() as client:
        r = await client.put(url, content=body, auth=(api_key, secret_key),
            headers={"Content-Type": "application/octet-stream"})
        return {"bucket": bucket, "key": key}


async def download_object(bucket: str, key: str, api_key: str, secret_key: str) -> dict:
    """Download from S3."""
    url = f"https://{bucket}.s3.amazonaws.com/{key}"
    async with AsyncClient() as client:
        r = await client.get(url, auth=(api_key, secret_key))
        return {"content": r.content, "key": key}


async def delete_object(bucket: str, key: str, api_key: str, secret_key: str) -> dict:
    """Delete S3 object."""
    url = f"https://{bucket}.s3.amazonaws.com/{key}"
    async with AsyncClient() as client:
        r = await client.delete(url, auth=(api_key, secret_key))
        return {"deleted": key}