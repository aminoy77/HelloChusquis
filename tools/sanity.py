from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class SanityTool(Tool):
    name = "sanity"
    description = "Sanity CMS - structured content management"

    def run(self, action: str, **kwargs) -> ToolResult:
        project_id = self.config.get("project_id")
        dataset = self.config.get("dataset", "production")
        token = self.config.get("token")

        if not project_id or not token:
            return ToolResult(success=False, error="Sanity credentials not configured")

        base_url = f"https://{project_id}.api.sanity.io/v2021-10-21/data/query/{dataset}"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            if action == "fetch":
                query = kwargs.get("query", "*[_type == \"document\"]")
                r = httpx.get(base_url, headers=headers, params={"query": query}, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("result", []))

            elif action == "mutate":
                mutations = kwargs.get("mutations", [])
                if not mutations:
                    return ToolResult(success=False, error="Mutations required")
                r = httpx.post(
                    f"https://{project_id}.api.sanity.io/v2021-10-21/data/mutate/{dataset}",
                    headers=headers,
                    json={"mutations": mutations},
                    timeout=30
                )
                return ToolResult(success=True, data=r.json())

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))