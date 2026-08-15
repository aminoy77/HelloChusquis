import time
from typing import Optional
from httpx import AsyncClient
import os
import httpx


def run(action: str, **kwargs) -> str:
    """Synchronous dispatcher for DataDog API actions."""
    api_key = kwargs.get("api_key") or os.getenv("DATADOG_API_KEY")
    if not api_key:
        return "Error: No DataDog API key found. Set DATADOG_API_KEY environment variable."

    import asyncio
    try:
        loop = asyncio.get_running_loop()
        import concurrent.futures
        fut = asyncio.run_coroutine_threadsafe(_run_async(action, api_key, kwargs), loop)
        return fut.result(timeout=30)
    except RuntimeError:
        return _run_sync(action, api_key, kwargs)


async def _run_async(action: str, api_key: str, kwargs: dict) -> str:
    """Async dispatcher for DataDog operations."""
    if action == "send_metric":
        return str(await send_metric(api_key, kwargs.get("metric", ""), kwargs.get("value", 0), kwargs.get("tags")))[2000]
    elif action == "get_metrics":
        return str(await get_metrics(api_key, kwargs.get("query", ""), kwargs.get("from_")))[2000]
    elif action == "create_dashboard":
        return str(await create_dashboard(api_key, kwargs.get("title", ""), kwargs.get("widgets", [])))[:2000]
    elif action == "get_incidents":
        return str(await get_incidents(api_key))[:2000]
    elif action == "create_monitor":
        return str(await create_monitor(api_key, kwargs.get("name", ""), kwargs.get("query", ""), kwargs.get("message", "")))[:2000]
    else:
        return f"Error: Unknown action '{action}'. Available: send_metric, get_metrics, create_dashboard, get_incidents, create_monitor"


def _run_sync(action: str, api_key: str, kwargs: dict) -> str:
    """Synchronous fallback using httpx.Client."""
    headers = {"DD-API-KEY": api_key}
    try:
        client = httpx.Client(timeout=30)
        if action == "send_metric":
            tags = kwargs.get("tags") or {}
            r = client.post("https://api.datadoghq.com/api/v1/series", json={
                "series": [{"metric": kwargs.get("metric", ""), "points": [[time.time(), kwargs.get("value", 0)]],
                           "type": "gauge", "tags": [f"{k}:{v}" for k, v in tags.items()]}]
            }, headers=headers)
            return str(r.json())[:2000]
        elif action == "get_metrics":
            r = client.get(f"https://api.datadoghq.com/api/v1/query?query={kwargs.get('query', '')}", headers=headers)
            return str(r.json())[:2000]
        elif action == "create_dashboard":
            r = client.post("https://api.datadoghq.com/api/v1/dashboard",
                           json={"title": kwargs.get("title", ""), "widgets": kwargs.get("widgets", [])}, headers=headers)
            return str(r.json())[:2000]
        elif action == "get_incidents":
            r = client.get("https://api.datadoghq.com/api/v1/incidents", headers=headers)
            return str(r.json())[:2000]
        elif action == "create_monitor":
            r = client.post("https://api.datadoghq.com/api/v1/monitor",
                           json={"name": kwargs.get("name", ""), "query": kwargs.get("query", ""),
                                 "message": kwargs.get("message", ""), "type": "query alert"}, headers=headers)
            return str(r.json())[:2000]
        else:
            return f"Error: Unknown action '{action}'. Available: send_metric, get_metrics, create_dashboard, get_incidents, create_monitor"
    except Exception as e:
        return f"Error: {str(e)}"


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