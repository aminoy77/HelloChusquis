from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class CalendlyTool(Tool):
    name = "calendly"
    description = "Calendly - meeting scheduling"

    def run(self, action: str, **kwargs) -> ToolResult:
        token = self.config.get("token")
        if not token:
            return ToolResult(success=False, error="Calendly token not configured")

        base_url = "https://api.calendly.com"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        try:
            if action == "list_events":
                r = httpx.get(f"{base_url}/scheduled_events", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("collection", []))

            elif action == "list_event_types":
                r = httpx.get(f"{base_url}/event_types", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("collection", []))

            elif action == "get_event":
                id = kwargs.get("id")
                if not id:
                    return ToolResult(success=False, error="Event UUID required")
                r = httpx.get(f"{base_url}/scheduled_events/{id}", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "list_users":
                r = httpx.get(f"{base_url}/users", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("collection", []))

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))