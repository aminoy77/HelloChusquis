from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class ClickUpTool(Tool):
    name = "clickup"
    description = "ClickUp - project management and tasks"

    def run(self, action: str, **kwargs) -> ToolResult:
        token = self.config.get("token")
        if not token:
            return ToolResult(success=False, error="ClickUp token not configured")

        base_url = "https://api.clickup.com/api/v2"
        headers = {"Authorization": token, "Content-Type": "application/json"}

        try:
            if action == "list_tasks":
                list_id = kwargs.get("list_id")
                if not list_id:
                    return ToolResult(success=False, error="list_id required")
                r = httpx.get(f"{base_url}/list/{list_id}/task", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("tasks", []))

            elif action == "create_task":
                list_id = kwargs.get("list_id")
                name = kwargs.get("name")
                if not list_id or not name:
                    return ToolResult(success=False, error="list_id and name required")
                payload = {"name": name, "description": kwargs.get("description", "")}
                r = httpx.post(f"{base_url}/list/{list_id}/task", headers=headers, json=payload, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "get_task":
                task_id = kwargs.get("id")
                if not task_id:
                    return ToolResult(success=False, error="Task ID required")
                r = httpx.get(f"{base_url}/task/{task_id}", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "list_lists":
                space_id = kwargs.get("space_id")
                if not space_id:
                    return ToolResult(success=False, error="space_id required")
                r = httpx.get(f"{base_url}/space/{space_id}/list", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("lists", []))

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))