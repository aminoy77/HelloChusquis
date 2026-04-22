from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class LinearTool(Tool):
    name = "linear"
    description = "Linear - issue tracking"

    def run(self, action: str, **kwargs) -> ToolResult:
        token = self.config.get("token")
        if not token:
            return ToolResult(success=False, error="Linear token not configured")

        base_url = "https://api.linear.app/graphql"
        headers = {"Authorization": token, "Content-Type": "application/json"}

        try:
            if action == "list_issues":
                query = """
                query { issues(first: 20) { nodes { id title state { name } } } }
                """
                r = httpx.post(base_url, headers=headers, json={"query": query}, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("data", {}).get("issues", {}).get("nodes", []))

            elif action == "create_issue":
                title = kwargs.get("title")
                if not title:
                    return ToolResult(success=False, error="Title required")
                query = "mutation CreateIssue($input: IssueCreateInput!) { issueCreate(input: $input) { success } }"
                variables = {"input": {"title": title}}
                r = httpx.post(base_url, headers=headers, json={"query": query, "variables": variables}, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "get_issue":
                id = kwargs.get("id")
                if not id:
                    return ToolResult(success=False, error="Issue ID required")
                query = "query GetIssue($id: String!) { issue(id: $id) { id title description } }"
                r = httpx.post(base_url, headers=headers, json={"query": query, "variables": {"id": id}}, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "list_teams":
                query = "{ teams { nodes { id name key } } }"
                r = httpx.post(base_url, headers=headers, json={"query": query}, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("data", {}).get("teams", {}).get("nodes", []))

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))