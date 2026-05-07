import time
from typing import Optional
from httpx import AsyncClient


async def send_metric(key: str, metric: str, value: float, tags: Optional[dict] = None) -> dict:
    """Send metric to DataDog."""
    if tags is None:
        tags = {}
    url = "https://api.datadoghq.com/api/v1/series"
    async with AsyncClient() as client:
        r = await client.post(url, json={
            "series": [{"metric": metric, "points": [[time.time(), value]], "type": "gauge", "tags": [f"{k}:{v}" for k, v in tags.items()]}]
        }, headers={"DD-API-KEY": key})
        return r.json()


async def get_metrics(key: str, query: str, from_: int = None) -> dict:
    """Query DataDog metrics."""
    url = f"https://api.datadoghq.com/api/v1/query?query={query}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"DD-API-KEY": key})
        return r.json()


async def create_dashboard(key: str, title: str, widgets: list) -> dict:
    """Create DataDog dashboard."""
    url = "https://api.datadoghq.com/api/v1/dashboard"
    async with AsyncClient() as client:
        r = await client.post(url, json={"title": title, "widgets": widgets}, headers={"DD-API-KEY": key})
        return r.json()


async def get_incidents(key: str) -> dict:
    """Get DataDog incidents."""
    url = "https://api.datadoghq.com/api/v1/incidents"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"DD-API-KEY": key})
        return r.json()


async def create_monitor(key: str, name: str, query: str, message: str) -> dict:
    """Create DataDog monitor."""
    url = "https://api.datadoghq.com/api/v1/monitor"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name, "query": query, "message": message, "type": "query alert"}, headers={"DD-API-KEY": key})
        return r.json()