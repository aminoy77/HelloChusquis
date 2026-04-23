from httpx import AsyncClient


async def upload_file(api_key: str, region: str, bucket: str, key: str, body: bytes) -> dict:
    """Upload file to DigitalOcean Spaces."""
    url = f"https://{region}.digitaloceanspaces.com/{bucket}/{key}"
    async with AsyncClient() as client:
        r = await client.put(url, content=body, headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/octet-stream"
        })
        return {"status": "uploaded", "key": key}


async def download_file(api_key: str, region: str, bucket: str, key: str) -> dict:
    """Download file from DigitalOcean Spaces."""
    url = f"https://{region}.digitaloceanspaces.com/{bucket}/{key}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return {"content": r.content, "key": key}


async def list_files(api_key: str, region: str, bucket: str) -> dict:
    """List files in DigitalOcean Space."""
    url = f"https://{region}.digitaloceanspaces.com/{bucket}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def delete_file(api_key: str, region: str, bucket: str, key: str) -> dict:
    """Delete file from DigitalOcean Space."""
    url = f"https://{region}.digitaloceanspaces.com/{bucket}/{key}"
    async with AsyncClient() as client:
        r = await client.delete(url, headers={"Authorization": f"Bearer {api_key}"})
        return {"status": "deleted"}


async def copy_file(api_key: str, region: str, bucket: str, source: str, dest: str) -> dict:
    """Copy file in DigitalOcean Space."""
    url = f"https://{region}.digitaloceanspaces.com/{bucket}/{dest}"
    headers = {"Authorization": f"Bearer {api_key}", "x-amz-copy-source": f"/{bucket}/{source}"}
    async with AsyncClient() as client:
        r = await client.put(url, headers=headers)
        return {"status": "copied"}