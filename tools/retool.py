from __future__ import annotations

import os
import httpx

PLUGIN_NAME = "retool"
PLUGIN_DESCRIPTION = "Retool - internal tools and dashboards"


def run(action: str, **kwargs) -> str:
    token = os.getenv("RETOOL_TOKEN")
    if not token:
        return "Error: No Retool token found. Set RETOOL_TOKEN environment variable."

    base_url = "https://api.retool.com/v1"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        if action == "list_resources":
            r = httpx.get(f"{base_url}/resources", headers=headers, timeout=30)
            data = r.json()
            return str(data.get("resources", data))

        elif action == "query_resource":
            id = kwargs.get("id")
            if not id:
                return "Error: Resource ID required for query_resource"
            r = httpx.get(f"{base_url}/resources/{id}", headers=headers, timeout=30)
            return _fmt(r)

        elif action == "list_apps":
            r = httpx.get(f"{base_url}/apps", headers=headers, timeout=30)
            data = r.json()
            return str(data.get("apps", data))

        elif action == "get_app":
            id = kwargs.get("id")
            if not id:
                return "Error: App ID required for get_app"
            r = httpx.get(f"{base_url}/apps/{id}", headers=headers, timeout=30)
            return _fmt(r)

        else:
            return f"Error: Unknown action '{action}'. Available: list_resources, query_resource, list_apps, get_app"
    except httpx.TimeoutException:
        return "Error: Request timed out after 30 seconds."
    except Exception as e:
        return f"Error: {e}"


def _fmt(r: httpx.Response) -> str:
    try:
        return str(r.json())
    except Exception:
        return r.text[:500]