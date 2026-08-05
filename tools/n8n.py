from __future__ import annotations

import os
import httpx

PLUGIN_NAME = "n8n"
PLUGIN_DESCRIPTION = "n8n - workflow automation"


def run(action: str, **kwargs) -> str:
    url = os.getenv("N8N_URL")
    token = os.getenv("N8N_API_KEY")
    if not url or not token:
        return "Error: n8n not configured. Set N8N_URL and N8N_API_KEY environment variables."

    base_url = f"{url.rstrip('/')}/api/v1"
    headers = {"X-N8N-API-KEY": token}

    try:
        if action == "list_workflows":
            r = httpx.get(f"{base_url}/workflows", headers=headers, timeout=30)
            data = r.json()
            return str(data.get("data", data))

        elif action == "activate_workflow":
            id = kwargs.get("id")
            if not id:
                return "Error: Workflow ID required for activate_workflow"
            r = httpx.post(f"{base_url}/workflows/{id}/activate", headers=headers, timeout=30)
            return _fmt(r)

        elif action == "deactivate_workflow":
            id = kwargs.get("id")
            if not id:
                return "Error: Workflow ID required for deactivate_workflow"
            r = httpx.post(f"{base_url}/workflows/{id}/deactivate", headers=headers, timeout=30)
            return _fmt(r)

        elif action == "trigger_workflow":
            id = kwargs.get("id")
            if not id:
                return "Error: Workflow ID required for trigger_workflow"
            r = httpx.post(f"{base_url}/workflows/{id}/run", headers=headers, json=kwargs.get("data", {}), timeout=30)
            return _fmt(r)

        else:
            return f"Error: Unknown action '{action}'. Available: list_workflows, activate_workflow, deactivate_workflow, trigger_workflow"
    except httpx.TimeoutException:
        return "Error: Request timed out after 30 seconds."
    except Exception as e:
        return f"Error: {e}"


def _fmt(r: httpx.Response) -> str:
    try:
        return str(r.json())
    except Exception:
        return r.text[:500]