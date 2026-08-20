from httpx import AsyncClient
import os
import re
import httpx


_INCIDENT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


def _incident_id(value: object) -> str:
    identifier = str(value or "")
    if not _INCIDENT_ID_RE.fullmatch(identifier):
        raise ValueError("Invalid PagerDuty incident ID.")
    return identifier


def run(action: str, **kwargs) -> str:
    """Synchronous dispatcher for PagerDuty API actions."""
    api_key = kwargs.get("api_key") or os.getenv("PAGERDUTY_API_KEY")
    if not api_key:
        return "Error: No PagerDuty API key found. Set PAGERDUTY_API_KEY environment variable."

    import asyncio
    try:
        loop = asyncio.get_running_loop()
        fut = asyncio.run_coroutine_threadsafe(_run_async(action, api_key, kwargs), loop)
        return fut.result(timeout=30)
    except RuntimeError:
        return _run_sync(action, api_key, kwargs)


async def _run_async(action: str, api_key: str, kwargs: dict) -> str:
    """Async dispatcher for PagerDuty operations."""
    if action == "create_incident":
        return str(await create_incident(api_key, kwargs.get("title", ""), kwargs.get("urgency", "high"), kwargs.get("service")))[2000]
    elif action == "list_incidents":
        return str(await list_incidents(api_key, kwargs.get("status", "triggered")))[2000]
    elif action == "get_incident":
        return str(await get_incident(api_key, kwargs.get("incident_id", "")))[:2000]
    elif action == "resolve_incident":
        return str(await resolve_incident(api_key, kwargs.get("incident_id", "")))[:2000]
    elif action == "create_maintenance_window":
        return str(await create_maintenance_window(api_key, kwargs.get("service_id", ""), kwargs.get("start", ""), kwargs.get("end", ""), kwargs.get("description", "")))[:2000]
    else:
        return f"Error: Unknown action '{action}'. Available: create_incident, list_incidents, get_incident, resolve_incident, create_maintenance_window"


def _run_sync(action: str, api_key: str, kwargs: dict) -> str:
    """Synchronous fallback using httpx.Client."""
    base_url = "https://api.pagerduty.com"
    headers = {"Authorization": f"Token token={api_key}", "Content-Type": "application/json"}
    try:
        client = httpx.Client(timeout=30)
        if action == "create_incident":
            r = client.post(f"{base_url}/incidents", json={
                "incident": {
                    "title": kwargs.get("title", ""),
                    "urgency": kwargs.get("urgency", "high"),
                    "service": {"id": kwargs.get("service")} if kwargs.get("service") else None
                }
            }, headers=headers)
            return str(r.json())[:2000]
        elif action == "list_incidents":
            status = kwargs.get("status", "triggered")
            r = client.get(f"{base_url}/incidents?statuses[]={status}", headers=headers)
            return str(r.json())[:2000]
        elif action == "get_incident":
            r = client.get(f"{base_url}/incidents/{_incident_id(kwargs.get('incident_id', ''))}", headers=headers)
            return str(r.json())[:2000]
        elif action == "resolve_incident":
            r = client.put(f"{base_url}/incidents/{_incident_id(kwargs.get('incident_id', ''))}",
                          json={"incident": {"type": "incident_reference", "status": "resolved"}}, headers=headers)
            return str(r.json())[:2000]
        elif action == "create_maintenance_window":
            r = client.post(f"{base_url}/maintenance_windows", json={
                "maintenance_window": {
                    "service": {"id": kwargs.get("service_id", "")},
                    "start_time": kwargs.get("start", ""),
                    "end_time": kwargs.get("end", ""),
                    "description": kwargs.get("description", "")
                }
            }, headers=headers)
            return str(r.json())[:2000]
        else:
            return f"Error: Unknown action '{action}'. Available: create_incident, list_incidents, get_incident, resolve_incident, create_maintenance_window"
    except Exception as e:
        return f"Error: {str(e)}"


class PagerDuty:
    """PagerDuty API wrapper."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.pagerduty.com"


async def create_incident(api_key: str, title: str, urgency: str = "high", service: str = None) -> dict:
    """Create Pagerduty incident."""
    url = "https://api.pagerduty.com/incidents"
    async with AsyncClient() as client:
        r = await client.post(url, json={
            "incident": {
                "title": title,
                "urgency": urgency,
                "service": {"id": service} if service else None
            }
        }, headers={"Authorization": f"Token token={api_key}", "Content-Type": "application/json"})
        return r.json()


async def list_incidents(api_key: str, status: str = "triggered") -> dict:
    """List pagerduty incidents."""
    url = f"https://api.pagerduty.com/incidents?statuses[]={status}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Token token={api_key}"})
        return r.json()


async def get_incident(api_key: str, incident_id: str) -> dict:
    """Get pagerduty incident."""
    url = f"https://api.pagerduty.com/incidents/{_incident_id(incident_id)}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Token token={api_key}"})
        return r.json()


async def resolve_incident(api_key: str, incident_id: str) -> dict:
    """Resolve pagerduty incident."""
    url = f"https://api.pagerduty.com/incidents/{_incident_id(incident_id)}"
    async with AsyncClient() as client:
        r = await client.put(url, json={"incident": {"type": "incident_reference", "status": "resolved"}}, headers={"Authorization": f"Token token={api_key}"})
        return r.json()


async def create_maintenance_window(api_key: str, service_id: str, start: str, end: str, description: str) -> dict:
    """Create maintenance window."""
    url = "https://api.pagerduty.com/maintenance_windows"
    async with AsyncClient() as client:
        r = await client.post(url, json={
            "maintenance_window": {
                "service": {"id": service_id},
                "start_time": start,
                "end_time": end,
                "description": description
            }
        }, headers={"Authorization": f"Token token={api_key}"})
        return r.json()