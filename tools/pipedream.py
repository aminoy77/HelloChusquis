from __future__ import annotations

import os
import httpx

PLUGIN_NAME = "pipedream"
PLUGIN_DESCRIPTION = "Pipedream - workflow automation"


def run(action: str, **kwargs) -> str:
    token = os.getenv("PIPEDREAM_TOKEN")
    if not token:
        return "Error: No Pipedream token found. Set PIPEDREAM_TOKEN environment variable."

    base_url = "https://api.pipedream.com/v1"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        if action == "list_sources":
            r = httpx.get(f"{base_url}/sources", headers=headers, timeout=30)
            data = r.json()
            return str(data.get("data", data))

        elif action == "list_workflows":
            r = httpx.get(f"{base_url}/workflows", headers=headers, timeout=30)
            data = r.json()
            return str(data.get("data", data))

        elif action == "create_workflow":
            name = kwargs.get("name")
            if not name:
                return "Error: name required for create_workflow"
            payload = {"name": name, "definition": kwargs.get("definition", {})}
            r = httpx.post(f"{base_url}/workflows", headers=headers, json=payload, timeout=30)
            return _fmt(r)

        elif action == "execute_action":
            component = kwargs.get("component")
            if not component:
                return "Error: component ID required for execute_action"
            r = httpx.post(f"{base_url}/components/{component}/execute", headers=headers, json=kwargs.get("props", {}), timeout=60)
            return _fmt(r)

        else:
            return f"Error: Unknown action '{action}'. Available: list_sources, list_workflows, create_workflow, execute_action"
    except httpx.TimeoutException:
        return "Error: Request timed out."
    except Exception as e:
        return f"Error: {e}"


def _fmt(r: httpx.Response) -> str:
    try:
        return str(r.json())
    except Exception:
        return r.text[:500]