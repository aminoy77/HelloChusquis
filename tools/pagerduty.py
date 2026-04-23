from  httpx import AsyncClient
from  typing import Any


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
    url = f"https://api.pagerduty.com/incidents/{incident_id}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Token token={api_key}"})
        return r.json()


async def resolve_incident(api_key: str, incident_id: str) -> dict:
    """Resolve pagerduty incident."""
    url = f"https://api.pagerduty.com/incidents/{incident_id}"
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