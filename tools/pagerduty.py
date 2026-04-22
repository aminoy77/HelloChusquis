from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class PagerDutyTool(Tool):
    name = "pagerduty"
    description = "PagerDuty incident management and on-call"

    def run(self, action: str, **kwargs) -> ToolResult:
        token = self.config.get("token")
        if not token:
            return ToolResult(success=False, error="PagerDuty token not configured")

        base_url = "https://api.pagerduty.com"
        headers = {"Authorization": f"Token token={token}", "Content-Type": "application/json", "Accept": "application/vnd.pagerduty+json;version=2"}

        try:
            if action == "list_incidents":
                r = httpx.get(f"{base_url}/incidents", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("incidents", []))

            elif action == "get_incident":
                id = kwargs.get("id")
                if not id:
                    return ToolResult(success=False, error="Incident ID required")
                r = httpx.get(f"{base_url}/incidents/{id}", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "list_services":
                r = httpx.get(f"{base_url}/services", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("services", []))

            elif action == "list_on_calls":
                r = httpx.get(f"{base_url}/on_calls", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("on_calls", []))

            elif action == "trigger_incident":
                title = kwargs.get("title")
                if not title:
                    return ToolResult(success=False, error="Title required")
                payload = {
                    "routing_key": self.config.get("routing_key", ""),
                    "event_action": "trigger",
                    "payload": {"summary": title, "severity": kwargs.get("severity", "critical")}
                }
                r = httpx.post("https://events.pagerduty.com/v2/enqueue", json=payload, timeout=30)
                return ToolResult(success=True, data=r.json())

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))