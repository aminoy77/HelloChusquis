from httpx import AsyncClient


async def create_zoom_meeting(topic: str, start_time: str, duration: int, api_key: str, secret: str) -> dict:
    """Create Zoom meeting."""
    url = "https://api.zoom.us/v2/users/me/meetings"
    headers = {"Authorization": f"Bearer {api_key}"}
    async with AsyncClient() as client:
        r = await client.post(url, json={
            "topic": topic,
            "type": 2,
            "start_time": start_time,
            "duration": duration
        }, headers=headers)
        return r.json()


async def list_meetings(api_key: str, secret: str) -> dict:
    """List Zoom meetings."""
    url = "https://api.zoom.us/v2/users/me/meetings"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def get_meeting(api_key: str, meeting_id: str) -> dict:
    """Get Zoom meeting details."""
    url = f"https://api.zoom.us/v2/meetings/{meeting_id}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def delete_meeting(api_key: str, meeting_id: str) -> dict:
    """Delete Zoom meeting."""
    url = f"https://api.zoom.us/v2/meetings/{meeting_id}"
    async with AsyncClient() as client:
        r = await client.delete(url, headers={"Authorization": f"Bearer {api_key}"})
        return {"status": "deleted"}


async def get_recordings(api_key: str, meeting_id: str) -> dict:
    """Get Zoom meeting recordings."""
    url = f"https://api.zoom.us/v2/meetings/{meeting_id}/recordings"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()