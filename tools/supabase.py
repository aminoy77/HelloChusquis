from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class SupabaseTool(Tool):
    name = "supabase"
    description = "Supabase PostgreSQL database, auth, and realtime"

    def run(self, action: str, **kwargs) -> ToolResult:
        url = self.config.get("url")
        key = self.config.get("key")

        if not url or not key:
            return ToolResult(success=False, error="Supabase credentials not configured")

        headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}

        try:
            table = kwargs.get("table", "")
            if not table:
                return ToolResult(success=False, error="Table name required")

            if action == "select":
                r = httpx.get(f"{url}/rest/v1/{table}", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "insert":
                data = kwargs.get("data", {})
                r = httpx.post(f"{url}/rest/v1/{table}", headers=headers, json=[data], timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "update":
                data = kwargs.get("data", {})
                pk = kwargs.get("id")
                if not pk:
                    return ToolResult(success=False, error="ID required for update")
                r = httpx.patch(f"{url}/rest/v1/{table}?id=eq.{pk}", headers=headers, json=data, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "delete":
                pk = kwargs.get("id")
                if not pk:
                    return ToolResult(success=False, error="ID required for delete")
                r = httpx.delete(f"{url}/rest/v1/{table}?id=eq.{pk}", headers=headers, timeout=30)
                return ToolResult(success=True, data={"deleted": True})

            elif action == "list_tables":
                r = httpx.get(f"{url}/rest/v1/", headers=headers, params={"select": "tablename"}, timeout=30)
                return ToolResult(success=True, data=r.json())

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))