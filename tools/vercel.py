from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class VercelTool(Tool):
    name = "vercel"
    description = "Vercel deployments and project management"

    def run(self, action: str, **kwargs) -> ToolResult:
        token = self.config.get("token")
        if not token:
            return ToolResult(success=False, error="Vercel token not configured")

        base_url = "https://api.vercel.com/v6"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            if action == "list_deployments":
                r = httpx.get(f"{base_url}/deployments", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("deployments", []))

            elif action == "get_deployment":
                id = kwargs.get("id")
                if not id:
                    return ToolResult(success=False, error="Deployment ID required")
                r = httpx.get(f"{base_url}/deployments/{id}", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "list_projects":
                r = httpx.get(f"{base_url}/projects", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("projects", []))

            elif action == "get_project":
                name = kwargs.get("name")
                if not name:
                    return ToolResult(success=False, error="Project name required")
                r = httpx.get(f"{base_url}/projects/{name}", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))