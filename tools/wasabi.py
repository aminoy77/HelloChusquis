from httpx import AsyncClient


async def upload_file(api_key: str, bucket: str, file_path: str, content: bytes) -> dict:
    """Upload file to Wasabi."""
    url = f"https://{bucket}.s3.wasabisys.com/{file_path}"
    async with AsyncClient() as client:
        r = await client.put(url, content=content, headers={"Authorization": f"Bearer {api_key}"})
        return {"status": "uploaded", "path": file_path}


async def download_file(api_key: str, bucket: str, file_path: str) -> dict:
    """Download file from Wasabi."""
    url = f"https://{bucket}.s3.wasabisys.com/{file_path}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return {"content": r.content, "path": file_path}


async def list_files(api_key: str, bucket: str, prefix: str = "") -> dict:
    """List files in Wasabi bucket."""
    url = f"https://{bucket}.s3.wasabisys.com/?prefix={prefix}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def delete_file(api_key: str, bucket: str, file_path: str) -> dict:
    """Delete file from Wasabi."""
    url = f"https://{bucket}.s3.wasabisys.com/{file_path}"
    async with AsyncClient() as client:
        r = await client.delete(url, headers={"Authorization": f"Bearer {api_key}"})
        return {"status": "deleted"}


async def copy_file(api_key: str, bucket: str, source: str, destination: str) -> dict:
    """Copy file in Wasabi."""
    url = f"https://{bucket}.s3.wasabisys.com/{destination}"
    async with AsyncClient() as client:
        r = await client.put(url, headers={
            "Authorization": f"Bearer {api_key}",
            "x-amz-copy-source": f"/{bucket}/{source}"
        })
        return {"status": "copied"}