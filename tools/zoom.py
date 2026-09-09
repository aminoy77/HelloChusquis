from httpx import AsyncClient
import os
import re
import httpx

_MEETING_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


def _meeting_id(value: object) -> str:
    identifier = str(value or "")
    if not _MEETING_ID_RE.fullmatch(identifier):
        raise ValueError("Invalid Zoom meeting ID.")
    return identifier


def run(action: str, **kwargs) -> str:
    """Synchronous dispatcher for Zoom API actions."""
    api_key = kwargs.get("api_key") or os.getenv("ZOOM_API_KEY")
    if not api_key:
        return "Error: No Zoom API key found. Set ZOOM_API_KEY environment variable."

    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return _run_sync(action, api_key, kwargs)
        return loop.run_until_complete(_run_async(action, api_key, kwargs))
    except RuntimeError:
        return _run_sync(action, api_key, kwargs)


async def _run_async(action: str, api_key: str, kwargs: dict) -> str:
    """Async dispatcher for Zoom operations."""
    if action == "create_meeting":
        return await create_zoom_meeting(kwargs.get("topic", ""), kwargs.get("start_time", ""), kwargs.get("duration", 30), api_key, api_key)
    elif action == "list_meetings":
        return await list_meetings(api_key, api_key)
    elif action == "get_meeting":
        return await get_meeting(api_key, kwargs.get("meeting_id", ""))
    elif action == "delete_meeting":
        return await delete_meeting(api_key, kwargs.get("meeting_id", ""))
    elif action == "get_recordings":
        return await get_recordings(api_key, kwargs.get("meeting_id", ""))
    else:
        return f"Error: Unknown action '{action}'. Available: create_meeting, list_meetings, get_meeting, delete_meeting, get_recordings"


def _run_sync(action: str, api_key: str, kwargs: dict) -> str:
    """Synchronous fallback using httpx.Client."""
    base_url = "https://api.zoom.us/v2"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        client = httpx.Client(timeout=30)
        if action == "create_meeting":
            r = client.post(f"{base_url}/users/me/meetings", json={"topic": kwargs.get("topic", ""), "type": 2, "start_time": kwargs.get("start_time", ""), "duration": kwargs.get("duration", 30)}, headers=headers)
            return str(r.json())[:2000]
        elif action == "list_meetings":
            r = client.get(f"{base_url}/users/me/meetings", headers=headers)
            return str(r.json())[:2000]
        elif action == "get_meeting":
            r = client.get(f"{base_url}/meetings/{_meeting_id(kwargs.get('meeting_id', ''))}", headers=headers)
            return str(r.json())[:2000]
        elif action == "delete_meeting":
            r = client.delete(f"{base_url}/meetings/{_meeting_id(kwargs.get('meeting_id', ''))}", headers=headers)
            return str(r.json())[:2000]
        elif action == "get_recordings":
            r = client.get(f"{base_url}/meetings/{_meeting_id(kwargs.get('meeting_id', ''))}/recordings", headers=headers)
            return str(r.json())[:2000]
        else:
            return f"Error: Unknown action '{action}'. Available: create_meeting, list_meetings, get_meeting, delete_meeting, get_recordings"
    except Exception as e:
        return f"Error: {str(e)}"


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
    url = f"https://api.zoom.us/v2/meetings/{_meeting_id(meeting_id)}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def delete_meeting(api_key: str, meeting_id: str) -> dict:
    """Delete Zoom meeting."""
    url = f"https://api.zoom.us/v2/meetings/{_meeting_id(meeting_id)}"
    async with AsyncClient() as client:
        await client.delete(url, headers={"Authorization": f"Bearer {api_key}"})
        return {"status": "deleted"}


async def get_recordings(api_key: str, meeting_id: str) -> dict:
    """Get Zoom meeting recordings."""
    url = f"https://api.zoom.us/v2/meetings/{_meeting_id(meeting_id)}/recordings"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()