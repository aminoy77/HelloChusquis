from httpx import AsyncClient


async def upload_file(account_id: str, access_key: str, secret_key: str, bucket: str, key: str, body: bytes) -> dict:
    """Upload file to Cloudflare R2."""
    url = f"https://{bucket}.{account_id}.r2.cloudflarestorage.com/{key}"
    async with AsyncClient() as client:
        r = await client.put(url, content=body, auth=(access_key, secret_key))
        return {"status": "uploaded", "key": key}


async def download_file(account_id: str, access_key: str, secret_key: str, bucket: str, key: str) -> dict:
    """Download file from Cloudflare R2."""
    url = f"https://{bucket}.{account_id}.r2.cloudflarestorage.com/{key}"
    async with AsyncClient() as client:
        r = await client.get(url, auth=(access_key, secret_key))
        return {"content": r.content, "key": key}


async def list_files(account_id: str, access_key: str, secret_key: str, bucket: str) -> dict:
    """List files in Cloudflare R2."""
    url = f"https://{bucket}.{account_id}.r2.cloudflarestorage.com/"
    async with AsyncClient() as client:
        r = await client.get(url, auth=(access_key, secret_key))
        return r.json()


async def delete_file(account_id: str, access_key: str, secret_key: str, bucket: str, key: str) -> dict:
    """Delete file from Cloudflare R2."""
    url = f"https://{bucket}.{account_id}.r2.cloudflarestorage.com/{key}"
    async with AsyncClient() as client:
        r = await client.delete(url, auth=(access_key, secret_key))
        return {"status": "deleted"}


async def get_signed_url(account_id: str, access_key: str, secret_key: str, bucket: str, key: str, expires: int = 3600) -> dict:
    """Generate signed URL for Cloudflare R2."""
    import hmac, hashlib, base64, time
    expiry = int(time.time()) + expires
    string_to_sign = f"GET\n/{key}\n{expiry}"
    sig = base64.b64encode(hmac.new(secret_key.encode(), string_to_sign.encode(), hashlib.sha256).digest()).decode()
    url = f"https://{bucket}.{account_id}.r2.cloudflarestorage.com/{key}?X-Amz-Expires={expiry}&X-Amz-Signature={sig}"
    return {"url": url}