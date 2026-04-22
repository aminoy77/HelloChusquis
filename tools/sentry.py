from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class SentryTool(Tool):
    name = "sentry"
    description = "Sentry error tracking and performance monitoring"

    def run(self, action: str, **kwargs) -> ToolResult:
        token = self.config.get("token")
        org = self.config.get("org")
        if not token or not org:
            return ToolResult(success=False, error="Sentry credentials not configured")

        base_url = f"https://sentry.io/api/0/organizations/{org}"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            if action == "list_issues":
                r = httpx.get(f"{base_url}/issues/", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=[
                    {"id": i.get("id"), "title": i.get("title"), "level": i.get("level"), "status": i.get("status")}
                    for i in data[:20]
                ])

            elif action == "get_issue":
                id = kwargs.get("id")
                if not id:
                    return ToolResult(success=False, error="Issue ID required")
                r = httpx.get(f"{base_url}/issues/{id}/", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "list_projects":
                r = httpx.get(f"{base_url}/projects/", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=[
                    {"id": p.get("id"), "name": p.get("name"), "slug": p.get("slug")}
                    for p in data
                ])

            elif action == "get_stats":
                id = kwargs.get("id")
                if not id:
                    return ToolResult(success=False, error="Project ID required")
                r = httpx.get(f"{base_url}/projects/{id}/stats/", headers=headers, params={"stat": "all"}, timeout=30)
                return ToolResult(success=True, data=r.json())

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))