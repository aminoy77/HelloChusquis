from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class RetoolTool(Tool):
    name = "retool"
    description = "Retool - internal tools and dashboards"

    def run(self, action: str, **kwargs) -> ToolResult:
        token = self.config.get("token")
        if not token:
            return ToolResult(success=False, error="Retool token not configured")

        base_url = "https://api.retool.com/v1"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        try:
            if action == "list_resources":
                r = httpx.get(f"{base_url}/resources", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("resources", []))

            elif action == "query_resource":
                id = kwargs.get("id")
                if not id:
                    return ToolResult(success=False, error="Resource ID required")
                r = httpx.get(f"{base_url}/resources/{id}", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "list_apps":
                r = httpx.get(f"{base_url}/apps", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("apps", []))

            elif action == "get_app":
                id = kwargs.get("id")
                if not id:
                    return ToolResult(success=False, error="App ID required")
                r = httpx.get(f"{base_url}/apps/{id}", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))