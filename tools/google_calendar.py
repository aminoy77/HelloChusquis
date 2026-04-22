from tools.base import BaseTool, ToolResult
import httpx
import os
import json
from datetime import datetime


PLUGIN_NAME = "google_calendar"
PLUGIN_DESCRIPTION = "Manage Google Calendar events"

GOOGLE_CALENDAR_SCHEMA = {
    "type": "function",
    "function": {
        "name": "google_calendar",
        "description": "Create, list, and manage Google Calendar events",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list_events", "create_event", "get_event", "delete_event", "quick_add"],
                    "description": "The Calendar action to perform"
                },
                "calendar_id": {"type": "string", "description": "Calendar ID (default: primary)"},
                "title": {"type": "string", "description": "Event title"},
                "description": {"type": "string", "description": "Event description"},
                "start_time": {"type": "string", "description": "Start time (ISO 8601)"},
                "end_time": {"type": "string", "description": "End time (ISO 8601)"},
                "location": {"type": "string", "description": "Event location"},
                "attendees": {"type": "string", "description": "Comma-separated attendee emails"},
                "event_id": {"type": "string", "description": "Event ID for get/delete"},
                "max_results": {"type": "number", "description": "Max events (default 10)"},
            },
            "required": ["action"]
        }
    }
}


def get_gcal_credentials() -> str:
    """Get Google Calendar OAuth token."""
    return os.getenv("GOOGLE_CALENDAR_TOKEN") or os.getenv("GCAL_TOKEN")


def run(action: str, calendar_id: str = "primary", title: str = "", description: str = "",
       start_time: str = "", end_time: str = "", location: str = "", attendees: str = "",
       event_id: str = "", max_results: int = 10) -> str:
    """Execute Google Calendar actions."""
    token = get_gcal_credentials()
    if not token:
        return "Error: Google Calendar token not found. Set GOOGLE_CALENDAR_TOKEN."
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    base_url = "https://www.googleapis.com/calendar/v3"
    
    try:
        client = httpx.Client(timeout=30)
        
        if action == "list_events":
            resp = client.get(
                f"{base_url}/calendars/{calendar_id}/events",
                headers=headers,
                params={"maxResults": max_results, "orderBy": "startTime", "singleEvents": True}
            )
            if resp.status_code == 200:
                events = resp.json().get("items", [])
                result = []
                for e in events[:max_results]:
                    start = e.get("start", {}).get("dateTime", e.get("start", {}).get("date", ""))
                    end = e.get("end", {}).get("dateTime", e.get("end", {}).get("date", ""))
                    summary = e.get("summary", "No title")
                    result.append(f"• {start[:16]}: {summary}")
                return "\n".join(result) if result else "No events found."
            return f"Error: {resp.status_code} - {resp.text[:200]}"
        
        elif action == "create_event":
            if not title:
                return "Error: title required for create_event"
            
            event = {"summary": title, "description": description}
            
            if start_time:
                event["start"] = {"dateTime": start_time, "timeZone": "UTC"}
            if end_time:
                event["end"] = {"dateTime": end_time, "timeZone": "UTC"}
            if location:
                event["location"] = location
            if attendees:
                emails = [{"email": e.strip()} for e in attendees.split(",")]
                event["attendees"] = emails
            
            resp = client.post(
                f"{base_url}/calendars/{calendar_id}/events",
                headers=headers,
                json=event
            )
            if resp.status_code == 200:
                e = resp.json()
                return f"Event created! :white_check_mark:\n{e.get('id')}\n{e.get('htmlLink')}"
            return f"Error: {resp.status_code} - {resp.text[:200]}"
        
        elif action == "get_event":
            if not event_id:
                return "Error: event_id required for get_event"
            
            resp = client.get(f"{base_url}/calendars/{calendar_id}/events/{event_id}", headers=headers)
            if resp.status_code == 200:
                e = resp.json()
                start = e.get("start", {}).get("dateTime", "N/A")
                end = e.get("end", {}).get("dateTime", "N/A")
                return f"{e.get('summary', 'No title')}\nStart: {start}\nEnd: {end}\n{e.get('htmlLink')}"
            return f"Error: {resp.status_code} - {resp.text[:200]}"
        
        elif action == "delete_event":
            if not event_id:
                return "Error: event_id required for delete_event"
            
            resp = client.delete(f"{base_url}/calendars/{calendar_id}/events/{event_id}", headers=headers)
            if resp.status_code == 204:
                return f"Event deleted! :white_check_mark:"
            return f"Error: {resp.status_code} - {resp.text[:200]}"
        
        elif action == "quick_add":
            if not title:
                return "Error: text required for quick_add"
            
            event = {"text": title}
            resp = client.post(
                f"{base_url}/calendars/{calendar_id}/events/quickAdd",
                headers=headers,
                json=event
            )
            if resp.status_code == 200:
                e = resp.json()
                return f"Event created! :white_check_mark:\n{e.get('id')}\n{e.get('htmlLink')}"
            return f"Error: {resp.status_code} - {resp.text[:200]}"
        
        else:
            return f"Error: Unknown action '{action}'. Available: list_events, create_event, get_event, delete_event, quick_add"
    
    except httpx.TimeoutException:
        return "Error: Request timed out after 30 seconds."
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    print("Google Calendar plugin loaded. Use 'google_calendar' tool in HelloChusquis.")