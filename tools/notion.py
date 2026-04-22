from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class NotionTool(Tool):
    name = "notion"
    description = "Notion - pages and databases"

    def run(self, action: str, **kwargs) -> ToolResult:
        token = self.config.get("token")
        if not token:
            return ToolResult(success=False, error="Notion token not configured")

        base_url = "https://api.notion.com/v1"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Notion-Version": "2022-06-28"}

        try:
            if action == "search":
                query = kwargs.get("query", "")
                payload = {"query": query} if query else {}
                r = httpx.post(f"{base_url}/search", headers=headers, json=payload, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("results", []))

            elif action == "get_page":
                page_id = kwargs.get("id")
                if not page_id:
                    return ToolResult(success=False, error="Page ID required")
                r = httpx.get(f"{base_url}/pages/{page_id}", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "create_page":
                parent_id = kwargs.get("parent_id")
                title = kwargs.get("title")
                if not parent_id or not title:
                    return ToolResult(success=False, error="parent_id and title required")
                title_block = {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": title}}]}}
                payload = {"parent": {"page_id": parent_id}, "children": [title_block]}
                r = httpx.post(f"{base_url}/blocks/{parent_id}/children", headers=headers, json=payload, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "list_databases":
                r = httpx.post(f"{base_url}/search", headers=headers, json={"filter": {"property": "object", "value": "database"}}, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("results", []))

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


def run(action: str = "list", **kwargs):
    tool = NotionTool()
    return tool.run(action, **kwargs)