from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class AirtableTool(Tool):
    name = "airtable"
    description = "Airtable - collaborative bases and tables"

    def run(self, action: str, **kwargs) -> ToolResult:
        token = self.config.get("token")
        base_id = self.config.get("base_id")
        if not token:
            return ToolResult(success=False, error="Airtable token not configured")

        base_url = f"https://api.airtable.com/v0/{base_id}"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            table = kwargs.get("table", "")
            if not table:
                return ToolResult(success=False, error="Table name required")

            if action == "list_records":
                r = httpx.get(f"{base_url}/{table}", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("records", []))

            elif action == "create_record":
                fields = kwargs.get("fields", {})
                if not fields:
                    return ToolResult(success=False, error="Fields required")
                r = httpx.post(f"{base_url}/{table}", headers=headers, json={"fields": fields}, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "update_record":
                id = kwargs.get("id")
                fields = kwargs.get("fields", {})
                if not id or not fields:
                    return ToolResult(success=False, error="ID and fields required")
                r = httpx.patch(f"{base_url}/{table}/{id}", headers=headers, json={"fields": fields}, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "delete_record":
                id = kwargs.get("id")
                if not id:
                    return ToolResult(success=False, error="Record ID required")
                r = httpx.delete(f"{base_url}/{table}/{id}", headers=headers, timeout=30)
                return ToolResult(success=True, data={"deleted": True})

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))