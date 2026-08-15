from __future__ import annotations

import os
import httpx

PLUGIN_NAME = "workato"
PLUGIN_DESCRIPTION = "Workato - enterprise integration"


def run(action: str, **kwargs) -> str:
    token = os.getenv("WORKATO_TOKEN")
    workspace = os.getenv("WORKATO_WORKSPACE")
    if not token or not workspace:
        return "Error: Workato not configured. Set WORKATO_TOKEN and WORKATO_WORKSPACE environment variables."

    base_url = "https://www.workato.com/api/rest"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        if action == "list_recipes":
            r = httpx.get(f"{base_url}/workspaces/{workspace}/recipes", headers=headers, timeout=30)
            data = r.json()
            return str(data.get("recipes", data))

        elif action == "start_recipe":
            id = kwargs.get("id")
            if not id:
                return "Error: Recipe ID required for start_recipe"
            r = httpx.post(f"{base_url}/workspaces/{workspace}/recipes/{id}/start", headers=headers, timeout=30)
            return _fmt(r)

        elif action == "stop_recipe":
            id = kwargs.get("id")
            if not id:
                return "Error: Recipe ID required for stop_recipe"
            r = httpx.post(f"{base_url}/workspaces/{workspace}/recipes/{id}/stop", headers=headers, timeout=30)
            return _fmt(r)

        elif action == "list_connectors":
            r = httpx.get(f"{base_url}/connectors", headers=headers, timeout=30)
            data = r.json()
            return str(data.get("connectors", data))

        else:
            return f"Error: Unknown action '{action}'. Available: list_recipes, start_recipe, stop_recipe, list_connectors"
    except httpx.TimeoutException:
        return "Error: Request timed out after 30 seconds."
    except Exception as e:
        return f"Error: {e}"


def _fmt(r: httpx.Response) -> str:
    try:
        return str(r.json())
    except Exception:
        return r.text[:500]