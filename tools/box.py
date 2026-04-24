from httpx import AsyncClient


async def upload_file(api_key: str, file_id: str, content: bytes, name: str) -> dict:
    """Upload file to Box."""
    url = f"https://upload.box.com/api/2.0/files/{file_id}/content"
    async with AsyncClient() as client:
        r = await client.post(url, content=content, headers={"Authorization": f"Bearer {api_key}"}, data={"attributes": f'{{"name":"{name}","parent":"{file_id}"}}'})
        return r.json()


async def get_file(api_key: str, file_id: str) -> dict:
    """Get Box file info."""
    url = f"https://api.box.com/2.0/files/{file_id}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def list_folder(api_key: str, folder_id: str = "0") -> dict:
    """List Box folder contents."""
    url = f"https://api.box.com/2.0/folders/{folder_id}/items"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def create_folder(api_key: str, name: str, parent_id: str = "0") -> dict:
    """Create Box folder."""
    url = "https://api.box.com/2.0/folders"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name, "parent": {"id": parent_id}}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def share_file(api_key: str, file_id: str) -> dict:
    """Create Box shared link."""
    url = f"https://api.box.com/2.0/files/{file_id}"
    async with AsyncClient() as client:
        r = await client.put(url, json={"shared_link": {"access": "open"}}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()