from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class BitbucketTool(Tool):
    name = "bitbucket"
    description = "Bitbucket - Git repositories"

    def run(self, action: str, **kwargs) -> ToolResult:
        username = self.config.get("username")
        app_password = self.config.get("app_password")
        if not username or not app_password:
            return ToolResult(success=False, error="Bitbucket credentials not configured")

        base_url = "https://api.bitbucket.org/2.0"
        auth = (username, app_password)

        try:
            if action == "list_repos":
                r = httpx.get(f"{base_url}/repositories/{username}", auth=auth, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("values", []))

            elif action == "get_repo":
                repo = kwargs.get("repo")
                if not repo:
                    return ToolResult(success=False, error="Repo name required")
                r = httpx.get(f"{base_url}/repositories/{username}/{repo}", auth=auth, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "list_pull_requests":
                repo = kwargs.get("repo")
                if not repo:
                    return ToolResult(success=False, error="Repo name required")
                r = httpx.get(f"{base_url}/repositories/{username}/{repo}/pullrequests", auth=auth, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("values", []))

            elif action == "create_pull_request":
                repo = kwargs.get("repo")
                title = kwargs.get("title")
                source = kwargs.get("source")
                target = kwargs.get("target", "main")
                if not repo or not title or not source:
                    return ToolResult(success=False, error="repo, title, and source required")
                payload = {"title": title, "source": {"branch": {"name": source}}, "destination": {"branch": {"name": target}}}
                r = httpx.post(f"{base_url}/repositories/{username}/{repo}/pullrequests", auth=auth, json=payload, timeout=30)
                return ToolResult(success=True, data=r.json())

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))