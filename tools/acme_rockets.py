from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from tools.base import Tool, ToolResult


class AcmeRocketsTool(Tool):
    name = "acme_rockets"
    description = "ACME Rockets API for spacecraft management and launch scheduling"

    def run(self, action: str, **kwargs) -> ToolResult:
        """Execute an action against the acme_rockets API."""
        api_key = self.config.get("api_key")
        if not api_key:
            return ToolResult(success=False, error=f"acme_rockets API key not configured")

        base_url = self.config.get("base_url", "https://api.example.com/v1")
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        try:
            if action == "list":
                r = httpx.get(f"{base_url}", headers=headers, params=kwargs, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, data=r.json())

            elif action == "get":
                item_id = kwargs.get("id")
                if not item_id:
                    return ToolResult(success=False, error="ID required for get action")
                r = httpx.get(f"{base_url}/{item_id}", headers=headers, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, data=r.json())

            elif action == "create":
                data = kwargs.get("data", {})
                if not data:
                    return ToolResult(success=False, error="Data required for create action")
                r = httpx.post(f"{base_url}", headers=headers, json=data, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, data=r.json())

            elif action == "update":
                item_id = kwargs.get("id")
                if not item_id:
                    return ToolResult(success=False, error="ID required for update action")
                data = kwargs.get("data", {})
                if not data:
                    return ToolResult(success=False, error="Data required for update action")
                r = httpx.put(f"{base_url}/{item_id}", headers=headers, json=data, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, data=r.json())

            elif action == "delete":
                item_id = kwargs.get("id")
                if not item_id:
                    return ToolResult(success=False, error="ID required for delete action")
                r = httpx.delete(f"{base_url}/{item_id}", headers=headers, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, data={})

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")

        except httpx.HTTPStatusError as e:
            return ToolResult(success=False, error=f"HTTP {e.response.status_code}: {e.response.text[:200]}")
        except Exception as e:
            return ToolResult(success=False, error=f"Request failed: {str(e)}")

def run(action: str = "list", **kwargs):
    """Entry point for the tool."""
    tool = AcmeRocketsTool()
    return tool.run(action, **kwargs)
