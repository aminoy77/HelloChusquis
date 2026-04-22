from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class AlgoliaTool(Tool):
    name = "algolia"
    description = "Algolia - search and analytics"

    def run(self, action: str, **kwargs) -> ToolResult:
        app_id = self.config.get("app_id")
        api_key = self.config.get("api_key")
        index = self.config.get("index", "default")

        if not app_id or not api_key:
            return ToolResult(success=False, error="Algolia credentials not configured")

        base_url = f"https://{app_id}-dsn.algolia.net/1/indexes/{index}"
        headers = {"X-Algolia-API-Key": api_key, "X-Algolia-Application-Id": app_id, "Content-Type": "application/json"}

        try:
            if action == "search":
                query = kwargs.get("query", "")
                r = httpx.post(base_url, headers=headers, json={"params": f"query={query}"}, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("hits", []))

            elif action == "add_object":
                data = kwargs.get("data", {})
                if not data:
                    return ToolResult(success=False, error="Object data required")
                r = httpx.post(base_url, headers=headers, json=data, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "delete_object":
                id = kwargs.get("id")
                if not id:
                    return ToolResult(success=False, error="Object ID required")
                r = httpx.delete(f"{base_url}/{id}", headers=headers, timeout=30)
                return ToolResult(success=True, data={"deleted": True})

            elif action == "search_settings":
                r = httpx.get(f"{base_url}/settings", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))