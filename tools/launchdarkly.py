from __future__ import annotations

import os
import httpx

PLUGIN_NAME = "launchdarkly"
PLUGIN_DESCRIPTION = "LaunchDarkly - feature flags management"


def run(action: str, **kwargs) -> str:
    token = os.getenv("LAUNCHDARKLY_TOKEN")
    project_key = os.getenv("LAUNCHDARKLY_PROJECT_KEY", "default")
    if not token:
        return "Error: No LaunchDarkly token found. Set LAUNCHDARKLY_TOKEN environment variable."

    base_url = "https://app.launchdarkly.com/api/v2"
    headers = {"Authorization": token, "Content-Type": "application/json"}

    try:
        if action == "list_flags":
            r = httpx.get(f"{base_url}/flags/{project_key}", headers=headers, timeout=30)
            data = r.json()
            return str(data.get("items", data))

        elif action == "get_flag":
            flag = kwargs.get("flag")
            if not flag:
                return "Error: flag key required for get_flag"
            r = httpx.get(f"{base_url}/flags/{project_key}/{flag}", headers=headers, timeout=30)
            return _fmt(r)

        elif action == "toggle_flag":
            flag = kwargs.get("flag")
            if not flag:
                return "Error: flag key required for toggle_flag"
            state = bool(kwargs.get("state", True))
            patch = [{"op": "replace", "path": "/on", "value": state}]
            r = httpx.patch(f"{base_url}/flags/{project_key}/{flag}", headers=headers, json=patch, timeout=30)
            return _fmt(r)

        elif action == "list_environments":
            r = httpx.get(f"{base_url}/projects/{project_key}/environments", headers=headers, timeout=30)
            data = r.json()
            return str(data.get("items", data))

        else:
            return f"Error: Unknown action '{action}'. Available: list_flags, get_flag, toggle_flag, list_environments"
    except httpx.TimeoutException:
        return "Error: Request timed out after 30 seconds."
    except Exception as e:
        return f"Error: {e}"


def _fmt(r: httpx.Response) -> str:
    try:
        return str(r.json())
    except Exception:
        return r.text[:500]