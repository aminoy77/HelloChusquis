from __future__ import annotations

import os
import httpx

PLUGIN_NAME = "algolia"
PLUGIN_DESCRIPTION = "Algolia - search and analytics"


def run(action: str, **kwargs) -> str:
    app_id = os.getenv("ALGOLIA_APP_ID")
    api_key = os.getenv("ALGOLIA_API_KEY")
    index = os.getenv("ALGOLIA_INDEX", kwargs.get("index", "default"))
    if not app_id or not api_key:
        return "Error: Algolia credentials not configured. Set ALGOLIA_APP_ID and ALGOLIA_API_KEY environment variables."

    base_url = f"https://{app_id}-dsn.algolia.net/1/indexes/{index}"
    headers = {
        "X-Algolia-API-Key": api_key,
        "X-Algolia-Application-Id": app_id,
        "Content-Type": "application/json",
    }

    try:
        if action == "search":
            query = kwargs.get("query", "")
            r = httpx.post(base_url, headers=headers, json={"params": f"query={query}"}, timeout=30)
            data = r.json()
            return str(data.get("hits", data))

        elif action == "add_object":
            data = kwargs.get("data", {})
            if not data:
                return "Error: data (object) required for add_object"
            r = httpx.post(base_url, headers=headers, json=data, timeout=30)
            return _fmt(r)

        elif action == "delete_object":
            id = kwargs.get("id")
            if not id:
                return "Error: id required for delete_object"
            r = httpx.delete(f"{base_url}/{id}", headers=headers, timeout=30)
            return _fmt(r)

        elif action == "search_settings":
            r = httpx.get(f"{base_url}/settings", headers=headers, timeout=30)
            return _fmt(r)

        else:
            return f"Error: Unknown action '{action}'. Available: search, add_object, delete_object, search_settings"
    except httpx.TimeoutException:
        return "Error: Request timed out after 30 seconds."
    except Exception as e:
        return f"Error: {e}"


def _fmt(r: httpx.Response) -> str:
    try:
        return str(r.json())
    except Exception:
        return r.text[:500]