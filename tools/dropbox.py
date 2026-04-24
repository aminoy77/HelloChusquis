from httpx import AsyncClient
import json


async def upload_file(access_token: str, path: str, content: bytes) -> dict:
    """Upload file to Dropbox."""
    url = "https://content.dropboxapi.com/2/files/upload"
    headers = {"Dropbox-API-Arg": json.dumps({"path": path, "mode": "add"})}
    async with AsyncClient() as client:
        r = await client.post(url, content=content, headers={"Authorization": f"Bearer {access_token}", **headers})
        return r.json()


async def download_file(access_token: str, path: str) -> dict:
    """Download file from Dropbox."""
    url = "https://content.dropboxapi.com/2/files/download"
    headers = {"Dropbox-API-Arg": json.dumps({"path": path})}
    async with AsyncClient() as client:
        r = await client.post(url, headers={"Authorization": f"Bearer {access_token}", **headers})
        return {"content": r.content, "path": path}


async def list_files(access_token: str, path: str = "") -> dict:
    """List files in Dropbox."""
    url = "https://api.dropboxapi.com/2/files/list_folder"
    async with AsyncClient() as client:
        r = await client.post(url, json={"path": path}, headers={"Authorization": f"Bearer {access_token}"})
        return r.json()


async def create_folder(access_token: str, path: str) -> dict:
    """Create folder in Dropbox."""
    url = "https://api.dropboxapi.com/2/files/create_folder_v2"
    async with AsyncClient() as client:
        r = await client.post(url, json={"path": path}, headers={"Authorization": f"Bearer {access_token}"})
        return r.json()


async def delete_file(access_token: str, path: str) -> dict:
    """Delete file from Dropbox."""
    url = "https://api.dropboxapi.com/2/files/delete_v2"
    async with AsyncClient() as client:
        r = await client.post(url, json={"path": path}, headers={"Authorization": f"Bearer {access_token}"})
        return r.json()


async def get_shared_link(access_token: str, path: str) -> dict:
    """Get shared link for Dropbox file."""
    url = "https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings"
    async with AsyncClient() as client:
        r = await client.post(url, json={"path": path}, headers={"Authorization": f"Bearer {access_token}"})
        return r.json()