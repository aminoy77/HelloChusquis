from httpx import AsyncClient


async def upload_file(api_key: str, path: str) -> dict:
    """Upload file to Backblaze B2."""
    url = "https://api.backblazeb2.com/b2api/v2/b2_upload_file"
    async with AsyncClient() as client:
        r = await client.post(url, json={"path": path}, headers={"Authorization": api_key})
        return r.json()


async def download_file(api_key: str, file_id: str) -> dict:
    """Download file from Backblaze B2."""
    url = f"https://api.backblazeb2.com/b2api/v2/b2_download_file_by_id?fileId={file_id}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": api_key})
        return r.json()


async def list_files(api_key: str, bucket_id: str) -> dict:
    """List files in Backblaze B2 bucket."""
    url = f"https://api.backblazeb2.com/b2api/v2/b2_list_file_versions?bucketId={bucket_id}"
    async with AsyncClient() as client:
        r = await client.post(url, headers={"Authorization": api_key})
        return r.json()


async def create_bucket(api_key: str, name: str, type: str = "private") -> dict:
    """Create Backblaze B2 bucket."""
    url = "https://api.backblazeb2.com/b2api/v2/b2_create_bucket"
    async with AsyncClient() as client:
        r = await client.post(url, json={"bucketName": name, "bucketType": type}, headers={"Authorization": api_key})
        return r.json()


async def delete_file(api_key: str, file_id: str) -> dict:
    """Delete file from Backblaze B2."""
    url = "https://api.backblazeb2.com/b2api/v2/b2_delete_file_version"
    async with AsyncClient() as client:
        r = await client.post(url, json={"fileId": file_id}, headers={"Authorization": api_key})
        return r.json()