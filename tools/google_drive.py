from httpx import AsyncClient


async def list_files(access_token: str, folder_id: str = "root") -> dict:
    """List Google Drive files."""
    url = "https://www.googleapis.com/drive/v3/files"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {access_token}"})
        return r.json()


async def upload_file(access_token: str, name: str, content: bytes, mime_type: str = "text/plain") -> dict:
    """Upload file to Google Drive."""
    url = "https://www.googleapis.com/upload/drive/v3/files"
    async with AsyncClient() as client:
        r = await client.post(url, content=content, headers={"Authorization": f"Bearer {access_token}"}, params={"uploadType": "multipart"})
        return r.json()


async def download_file(access_token: str, file_id: str) -> dict:
    """Download file from Google Drive."""
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {access_token}"})
        return r.json()


async def create_folder(access_token: str, name: str, parent_id: str = None) -> dict:
    """Create folder in Google Drive."""
    url = "https://www.googleapis.com/drive/v3/files"
    metadata = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        metadata["parents"] = [parent_id]
    async with AsyncClient() as client:
        r = await client.post(url, json=metadata, headers={"Authorization": f"Bearer {access_token}"})
        return r.json()


async def share_file(access_token: str, file_id: str, email: str) -> dict:
    """Share Google Drive file."""
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions"
    async with AsyncClient() as client:
        r = await client.post(url, json={"type": "user", "role": "reader", "emailAddress": email}, headers={"Authorization": f"Bearer {access_token}"})
        return r.json()


async def search_files(access_token: str, query: str) -> dict:
    """Search Google Drive files."""
    url = "https://www.googleapis.com/drive/v3/files"
    async with AsyncClient() as client:
        r = await client.get(url, params={"q": query}, headers={"Authorization": f"Bearer {access_token}"})
        return r.json()