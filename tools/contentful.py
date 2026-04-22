from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class ContentfulTool(Tool):
    name = "contentful"
    description = "Contentful CMS - content management"

    def run(self, action: str, **kwargs) -> ToolResult:
        space_id = self.config.get("space_id")
        access_token = self.config.get("access_token")
        if not space_id or not access_token:
            return ToolResult(success=False, error="Contentful credentials not configured")

        base_url = f"https://cdn.contentful.com/spaces/{space_id}"
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            if action == "list_entries":
                r = httpx.get(f"{base_url}/entries", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("items", []))

            elif action == "get_entry":
                id = kwargs.get("id")
                if not id:
                    return ToolResult(success=False, error="Entry ID required")
                r = httpx.get(f"{base_url}/entries/{id}", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "list_assets":
                r = httpx.get(f"{base_url}/assets", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("items", []))

            elif action == "list_content_types":
                r = httpx.get(f"{base_url}/content_types", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("items", []))

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))