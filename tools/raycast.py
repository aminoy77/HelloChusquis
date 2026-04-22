from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class RaycastTool(Tool):
    name = "raycast"
    description = "Raycast - app shortcuts and extensions"

    def run(self, action: str, **kwargs) -> ToolResult:
        token = self.config.get("token")
        if not token:
            return ToolResult(success=False, error="Raycast token not configured")

        base_url = "https://api.raycast.com/v1"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        try:
            if action == "list_extensions":
                r = httpx.get(f"{base_url}/extensions", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("extensions", []))

            elif action == "launch_extension":
                id = kwargs.get("id")
                if not id:
                    return ToolResult(success=False, error="Extension ID required")
                r = httpx.post(f"{base_url}/extensions/{id}/launch", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "list_shortcuts":
                r = httpx.get(f"{base_url}/shortcuts", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("items", []))

            elif action == "run_shortcut":
                id = kwargs.get("id")
                params = kwargs.get("params", {})
                if not id:
                    return ToolResult(success=False, error="Shortcut ID required")
                r = httpx.post(f"{base_url}/shortcuts/{id}/run", headers=headers, json=params, timeout=30)
                return ToolResult(success=True, data=r.json())

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))