from __future__ import annotations

import os
import httpx

PLUGIN_NAME = "contentful"
PLUGIN_DESCRIPTION = "Contentful CMS - content management"


def run(action: str, **kwargs) -> str:
    space_id = os.getenv("CONTENTFUL_SPACE_ID")
    access_token = os.getenv("CONTENTFUL_ACCESS_TOKEN")
    if not space_id or not access_token:
        return "Error: Contentful credentials not configured. Set CONTENTFUL_SPACE_ID and CONTENTFUL_ACCESS_TOKEN environment variables."

    base_url = f"https://cdn.contentful.com/spaces/{space_id}"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        if action == "list_entries":
            r = httpx.get(f"{base_url}/entries", headers=headers, timeout=30)
            data = r.json()
            return str(data.get("items", []))

        elif action == "get_entry":
            id = kwargs.get("id")
            if not id:
                return "Error: Entry ID required for get_entry"
            r = httpx.get(f"{base_url}/entries/{id}", headers=headers, timeout=30)
            return _fmt(r)

        elif action == "list_assets":
            r = httpx.get(f"{base_url}/assets", headers=headers, timeout=30)
            data = r.json()
            return str(data.get("items", []))

        elif action == "list_content_types":
            r = httpx.get(f"{base_url}/content_types", headers=headers, timeout=30)
            data = r.json()
            return str(data.get("items", []))

        else:
            return f"Error: Unknown action '{action}'. Available: list_entries, get_entry, list_assets, list_content_types"
    except httpx.TimeoutException:
        return "Error: Request timed out after 30 seconds."
    except Exception as e:
        return f"Error: {e}"


def _fmt(r: httpx.Response) -> str:
    try:
        return str(r.json())
    except Exception:
        return r.text[:500]