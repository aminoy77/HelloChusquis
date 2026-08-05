from httpx import AsyncClient
import os
import httpx


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


def run(action: str, **kwargs) -> str:
    """Synchronous dispatcher for Google Calendar API actions."""
    api_key = kwargs.get("api_key") or os.getenv("GOOGLE_CALENDAR_API_KEY")
    if not api_key:
        return "Error: No Google Calendar API key found. Set GOOGLE_CALENDAR_API_KEY environment variable."
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return _run_sync(action, api_key, kwargs)
        return loop.run_until_complete(_run_async(action, api_key, kwargs))
    except RuntimeError:
        return _run_sync(action, api_key, kwargs)


async def _run_async(action: str, api_key: str, kwargs: dict) -> str:
    """Async dispatcher for Google Calendar operations."""
    if action == "create_event":
        return str(await create_event(kwargs.get("summary", ""), kwargs.get("start", ""), kwargs.get("end", ""), api_key, **kwargs))
    elif action == "list_events":
        return str(await list_events(api_key, kwargs.get("max_results", 10)))
    elif action == "get_event":
        return str(await get_event(kwargs.get("event_id", ""), api_key))
    elif action == "update_event":
        return str(await update_event(kwargs.get("event_id", ""), kwargs.get("summary", ""), api_key))
    elif action == "delete_event":
        return str(await delete_event(kwargs.get("event_id", ""), api_key))
    else:
        return f"Error: Unknown action '{action}'. Available: create_event, list_events, get_event, update_event, delete_event"


def _run_sync(action: str, api_key: str, kwargs: dict) -> str:
    """Synchronous fallback using httpx.Client."""
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        client = httpx.Client(timeout=30)
        if action == "create_event":
            r = client.post("https://www.googleapis.com/calendar/v3/calendars/primary/events",
                           json={"summary": kwargs.get("summary", ""), "start": {"dateTime": kwargs.get("start", "")}, "end": {"dateTime": kwargs.get("end", "")}},
                           headers=headers)
            return str(r.json())[:2000]
        elif action == "list_events":
            r = client.get("https://www.googleapis.com/calendar/v3/calendars/primary/events",
                          params={"maxResults": kwargs.get("max_results", 10)}, headers=headers)
            return str(r.json())[:2000]
        elif action == "get_event":
            r = client.get(f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{kwargs.get('event_id', '')}",
                          headers=headers)
            return str(r.json())[:2000]
        elif action == "update_event":
            r = client.patch(f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{kwargs.get('event_id', '')}",
                           json={"summary": kwargs.get("summary", "")}, headers=headers)
            return str(r.json())[:2000]
        elif action == "delete_event":
            r = client.delete(f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{kwargs.get('event_id', '')}",
                             headers=headers)
            return str({"deleted": True})
        else:
            return f"Error: Unknown action '{action}'. Available: create_event, list_events, get_event, update_event, delete_event"
    except Exception as e:
        return f"Error: {str(e)}"