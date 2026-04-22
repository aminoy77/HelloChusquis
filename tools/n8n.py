from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class N8nTool(Tool):
    name = "n8n"
    description = "n8n - workflow automation"

    def run(self, action: str, **kwargs) -> ToolResult:
        url = self.config.get("url")
        token = self.config.get("token")
        if not url or not token:
            return ToolResult(success=False, error="n8n URL and token not configured")

        base_url = f"{url.rstrip('/')}/api/v1"
        headers = {"X-N8N-API-KEY": token}

        try:
            if action == "list_workflows":
                r = httpx.get(f"{base_url}/workflows", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("data", []))

            elif action == "activate_workflow":
                id = kwargs.get("id")
                if not id:
                    return ToolResult(success=False, error="Workflow ID required")
                r = httpx.post(f"{base_url}/workflows/{id}/activate", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "deactivate_workflow":
                id = kwargs.get("id")
                if not id:
                    return ToolResult(success=False, error="Workflow ID required")
                r = httpx.post(f"{base_url}/workflows/{id}/deactivate", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "trigger_workflow":
                id = kwargs.get("id")
                if not id:
                    return ToolResult(success=False, error="Workflow ID required")
                r = httpx.post(f"{base_url}/webhooks/{id}", headers=headers, json=kwargs.get("data", {}), timeout=30)
                return ToolResult(success=True, data=r.json())

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))