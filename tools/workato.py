from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class WorkatoTool(Tool):
    name = "workato"
    description = "Workato - enterprise integration"

    def run(self, action: str, **kwargs) -> ToolResult:
        token = self.config.get("token")
        workspace = self.config.get("workspace")
        if not token or not workspace:
            return ToolResult(success=False, error="Workato token and workspace required")

        base_url = "https://www.workato.com/api/rest"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        try:
            if action == "list_recipes":
                r = httpx.get(f"{base_url}/workspaces/{workspace}/recipes", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("recipes", []))

            elif action == "start_recipe":
                id = kwargs.get("id")
                if not id:
                    return ToolResult(success=False, error="Recipe ID required")
                r = httpx.post(f"{base_url}/workspaces/{workspace}/recipes/{id}/start", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "stop_recipe":
                id = kwargs.get("id")
                if not id:
                    return ToolResult(success=False, error="Recipe ID required")
                r = httpx.post(f"{base_url}/workspaces/{workspace}/recipes/{id}/stop", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "list_connectors":
                r = httpx.get(f"{base_url}/connectors", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("connectors", []))

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))