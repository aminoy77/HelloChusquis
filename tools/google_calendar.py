from httpx import AsyncClient


async def create_event(summary: str, start: str, end: str, api_key: str, **kwargs) -> dict:
    """Create Google Calendar event."""
    url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
    async with AsyncClient() as client:
        r = await client.post(url, json={"summary": summary, "start": {"dateTime": start}, "end": {"dateTime": end}, **kwargs}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def list_events(api_key: str, max_results: int = 10) -> dict:
    """List Google Calendar events."""
    url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
    async with AsyncClient() as client:
        r = await client.get(url, params={"maxResults": max_results}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def get_event(event_id: str, api_key: str) -> dict:
    """Get Google Calendar event."""
    url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def update_event(event_id: str, summary: str, api_key: str) -> dict:
    """Update Google Calendar event."""
    url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}"
    async with AsyncClient() as client:
        r = await client.patch(url, json={"summary": summary}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def delete_event(event_id: str, api_key: str) -> dict:
    """Delete Google Calendar event."""
    url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}"
    async with AsyncClient() as client:
        r = await client.delete(url, headers={"Authorization": f"Bearer {api_key}"})
        return {"deleted": True}