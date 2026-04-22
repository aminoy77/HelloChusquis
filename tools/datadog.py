from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class DatadogTool(Tool):
    name = "datadog"
    description = "Datadog monitoring, metrics, and APM"

    def run(self, action: str, **kwargs) -> ToolResult:
        api_key = self.config.get("api_key")
        app_key = self.config.get("app_key")
        if not api_key or not app_key:
            return ToolResult(success=False, error="Datadog credentials not configured")

        base_url = "https://api.datadoghq.com/api"
        headers = {"DD-API-KEY": api_key, "DD-APPLICATION-KEY": app_key}

        try:
            if action == "query_metrics":
                query = kwargs.get("query")
                if not query:
                    return ToolResult(success=False, error="Query required")
                r = httpx.get(
                    f"{base_url}/v1/query",
                    headers=headers,
                    params={"query": query},
                    timeout=30
                )
                return ToolResult(success=True, data=r.json())

            elif action == "list_hosts":
                r = httpx.get(f"{base_url}/v1/hosts", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "get_services":
                r = httpx.get(f"{base_url}/v1/services", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "list_monitors":
                r = httpx.get(f"{base_url}/v1/monitor", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=[
                    {"id": m.get("id"), "name": m.get("name"), "state": m.get("state")}
                    for m in data
                ])

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))