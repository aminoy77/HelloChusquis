from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class MakeTool(Tool):
    name = "make"
    description = "Make (Integromat) - visual automation"

    def run(self, action: str, **kwargs) -> ToolResult:
        token = self.config.get("token")
        if not token:
            return ToolResult(success=False, error="Make API key not configured")

        base_url = "https://api.make.com/api/v3"
        headers = {"Authorization": token, "Content-Type": "application/json"}

        try:
            if action == "list_scenarios":
                r = httpx.get(f"{base_url}/scenarios", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("scenarios", []))

            elif action == "activate_scenario":
                id = kwargs.get("id")
                if not id:
                    return ToolResult(success=False, error="Scenario ID required")
                r = httpx.post(f"{base_url}/scenarios/{id}/activate", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "deactivate_scenario":
                id = kwargs.get("id")
                if not id:
                    return ToolResult(success=False, error="Scenario ID required")
                r = httpx.post(f"{base_url}/scenarios/{id}/deactivate", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "run_scenario":
                id = kwargs.get("id")
                if not id:
                    return ToolResult(success=False, error="Scenario ID required")
                r = httpx.post(f"{base_url}/scenarios/{id}/run", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "get_runs":
                id = kwargs.get("id")
                limit = kwargs.get("limit", 10)
                if not id:
                    return ToolResult(success=False, error="Scenario ID required")
                r = httpx.get(f"{base_url}/scenarios/{id}/runs", headers=headers, params={"limit": limit}, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("runs", []))

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))