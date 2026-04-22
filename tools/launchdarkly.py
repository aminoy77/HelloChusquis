from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class LaunchDarklyTool(Tool):
    name = "launchdarkly"
    description = "LaunchDarkly - feature flags management"

    def run(self, action: str, **kwargs) -> ToolResult:
        token = self.config.get("token")
        project_key = self.config.get("project_key", "default")
        if not token:
            return ToolResult(success=False, error="LaunchDarkly token not configured")

        base_url = "https://app.launchdarkly.com/api/v2"
        headers = {"Authorization": token, "Content-Type": "application/json"}

        try:
            if action == "list_flags":
                r = httpx.get(f"{base_url}/flags/{project_key}", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("items", []))

            elif action == "get_flag":
                flag = kwargs.get("flag")
                if not flag:
                    return ToolResult(success=False, error="Flag key required")
                r = httpx.get(f"{base_url}/flags/{project_key}/{flag}", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "toggle_flag":
                flag = kwargs.get("flag")
                state = kwargs.get("state", True)
                if not flag:
                    return ToolResult(success=False, error="Flag key required")
                patch = [{"op": "replace", "path": "/on", "value": state}]
                r = httpx.patch(f"{base_url}/flags/{project_key}/{flag}", headers=headers, json=patch, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "list_environments":
                r = httpx.get(f"{base_url}/projects/{project_key}/environments", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("items", []))

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))