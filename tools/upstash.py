from __future__ import annotations

import os
import httpx

PLUGIN_NAME = "upstash"
PLUGIN_DESCRIPTION = "Upstash - Redis serverless database"


def run(action: str, **kwargs) -> str:
    url = os.getenv("UPSTASH_REDIS_REST_URL")
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    if not url or not token:
        return "Error: Upstash credentials not configured. Set UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN environment variables."

    base_url = url.rstrip("/")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        if action == "get":
            key = kwargs.get("key")
            if not key:
                return "Error: key required for get"
            r = httpx.get(f"{base_url}/get/{key}", headers=headers, timeout=30)
            return _fmt(r)

        elif action == "set":
            key = kwargs.get("key")
            value = kwargs.get("value")
            if not key or value is None:
                return "Error: key and value required for set"
            ex = kwargs.get("ttl", 0)
            path = f"{base_url}/set/{key}"
            if ex:
                path += f"/ex/{int(ex)}"
            r = httpx.post(path, headers=headers, json=str(value), timeout=30)
            return _fmt(r)

        elif action == "incr":
            key = kwargs.get("key")
            if not key:
                return "Error: key required for incr"
            r = httpx.post(f"{base_url}/incr/{key}", headers=headers, timeout=30)
            return _fmt(r)

        elif action == "del":
            key = kwargs.get("key")
            if not key:
                return "Error: key required for del"
            r = httpx.post(f"{base_url}/del/{key}", headers=headers, timeout=30)
            return _fmt(r)

        elif action == "ping":
            r = httpx.get(f"{base_url}/ping", headers=headers, timeout=30)
            return _fmt(r)

        else:
            return f"Error: Unknown action '{action}'. Available: get, set, incr, del, ping"
    except httpx.TimeoutException:
        return "Error: Request timed out after 30 seconds."
    except Exception as e:
        return f"Error: {e}"


def _fmt(r: httpx.Response) -> str:
    try:
        return str(r.json())
    except Exception:
        return r.text[:500]