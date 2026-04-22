from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class PipedreamTool(Tool):
    name = "pipedream"
    description = "Pipedream - workflow automation"

    def run(self, action: str, **kwargs) -> ToolResult:
        token = self.config.get("token")
        if not token:
            return ToolResult(success=False, error="Pipedream token not configured")

        base_url = "https://api.pipedream.com/v2"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            if action == "list_sources":
                r = httpx.get(f"{base_url}/sources", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("data", []))

            elif action == "list_workflows":
                r = httpx.get(f"{base_url}/workflows", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("data", []))

            elif action == "create_workflow":
                name = kwargs.get("name")
                if not name:
                    return ToolResult(success=False, error="Name required")
                payload = {"name": name, "definition": kwargs.get("definition", {})}
                r = httpx.post(f"{base_url}/workflows", headers=headers, json=payload, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "execute_action":
                component = kwargs.get("component")
                props = kwargs.get("props", {})
                if not component:
                    return ToolResult(success=False, error="Component ID required")
                r = httpx.post(f"{base_url}/components/{component}/execute", headers=headers, json=props, timeout=60)
                return ToolResult(success=True, data=r.json())

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))