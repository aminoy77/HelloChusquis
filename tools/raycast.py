from __future__ import annotations

import os
import httpx

PLUGIN_NAME = "raycast"
PLUGIN_DESCRIPTION = "Raycast - app shortcuts and extensions"


def run(action: str, **kwargs) -> str:
    token = os.getenv("RAYCAST_TOKEN")
    if not token:
        return "Error: No Raycast token found. Set RAYCAST_TOKEN environment variable."

    base_url = "https://api.raycast.com/v1"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        if action == "list_extensions":
            r = httpx.get(f"{base_url}/extensions", headers=headers, timeout=30)
            data = r.json()
            return str(data.get("extensions", data))

        elif action == "launch_extension":
            id = kwargs.get("id")
            if not id:
                return "Error: Extension ID required for launch_extension"
            r = httpx.post(f"{base_url}/extensions/{id}/launch", headers=headers, timeout=30)
            return _fmt(r)

        elif action == "list_shortcuts":
            r = httpx.get(f"{base_url}/shortcuts", headers=headers, timeout=30)
            data = r.json()
            return str(data.get("items", data))

        elif action == "run_shortcut":
            id = kwargs.get("id")
            if not id:
                return "Error: Shortcut ID required for run_shortcut"
            r = httpx.post(f"{base_url}/shortcuts/{id}/run", headers=headers, json=kwargs.get("params", {}), timeout=30)
            return _fmt(r)

        else:
            return f"Error: Unknown action '{action}'. Available: list_extensions, launch_extension, list_shortcuts, run_shortcut"
    except httpx.TimeoutException:
        return "Error: Request timed out after 30 seconds."
    except Exception as e:
        return f"Error: {e}"


def _fmt(r: httpx.Response) -> str:
    try:
        return str(r.json())
    except Exception:
        return r.text[:500]