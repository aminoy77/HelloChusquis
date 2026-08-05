from __future__ import annotations

import os
import httpx

PLUGIN_NAME = "make"
PLUGIN_DESCRIPTION = "Make (Integromat) - visual automation"


def run(action: str, **kwargs) -> str:
    token = os.getenv("MAKE_API_KEY")
    if not token:
        return "Error: No Make API key found. Set MAKE_API_KEY environment variable."

    base_url = "https://api.make.com/api/v3"
    headers = {"Authorization": token, "Content-Type": "application/json"}

    try:
        if action == "list_scenarios":
            r = httpx.get(f"{base_url}/scenarios", headers=headers, timeout=30)
            data = r.json()
            return str(data.get("scenarios", data))

        elif action == "activate_scenario":
            id = kwargs.get("id")
            if not id:
                return "Error: Scenario ID required for activate_scenario"
            r = httpx.post(f"{base_url}/scenarios/{id}/activate", headers=headers, timeout=30)
            return _fmt(r)

        elif action == "deactivate_scenario":
            id = kwargs.get("id")
            if not id:
                return "Error: Scenario ID required for deactivate_scenario"
            r = httpx.post(f"{base_url}/scenarios/{id}/deactivate", headers=headers, timeout=30)
            return _fmt(r)

        elif action == "run_scenario":
            id = kwargs.get("id")
            if not id:
                return "Error: Scenario ID required for run_scenario"
            r = httpx.post(f"{base_url}/scenarios/{id}/run", headers=headers, timeout=30)
            return _fmt(r)

        elif action == "get_runs":
            id = kwargs.get("id")
            if not id:
                return "Error: Scenario ID required for get_runs"
            r = httpx.get(f"{base_url}/scenarios/{id}/runs", headers=headers, params={"limit": kwargs.get("limit", 10)}, timeout=30)
            data = r.json()
            return str(data.get("runs", data))

        else:
            return f"Error: Unknown action '{action}'. Available: list_scenarios, activate_scenario, deactivate_scenario, run_scenario, get_runs"
    except httpx.TimeoutException:
        return "Error: Request timed out after 30 seconds."
    except Exception as e:
        return f"Error: {e}"


def _fmt(r: httpx.Response) -> str:
    try:
        return str(r.json())
    except Exception:
        return r.text[:500]