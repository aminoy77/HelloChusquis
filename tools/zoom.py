from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class ZoomTool(Tool):
    name = "zoom"
    description = "Zoom - video meetings and recordings"

    def run(self, action: str, **kwargs) -> ToolResult:
        token = self.config.get("token")
        if not token:
            return ToolResult(success=False, error="Zoom token not configured")

        base_url = "https://api.zoom.us/v2"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        try:
            if action == "list_meetings":
                r = httpx.get(f"{base_url}/users/me/meetings", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("meetings", []))

            elif action == "create_meeting":
                topic = kwargs.get("topic")
                if not topic:
                    return ToolResult(success=False, error="Topic required")
                payload = {"topic": topic, "type": kwargs.get("type", 2), "duration": kwargs.get("duration", 60)}
                r = httpx.post(f"{base_url}/users/me/meetings", headers=headers, json=payload, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "get_meeting":
                id = kwargs.get("id")
                if not id:
                    return ToolResult(success=False, error="Meeting ID required")
                r = httpx.get(f"{base_url}/meetings/{id}", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "list_recordings":
                r = httpx.get(f"{base_url}/users/me/recordings", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("meetings", []))

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))