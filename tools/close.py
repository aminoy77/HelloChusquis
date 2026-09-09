"""Safe Close CRM integration."""

from __future__ import annotations

from typing import Any

import httpx

from tools.base import BaseTool, ToolResult


_BASE_URL = "https://api.close.com/api/v1"
_MAX_OUTPUT_CHARS = 2000


def _bounded_response(response: httpx.Response) -> str:
    """Serialize a remote response within the agent's output budget."""
    return str(response.json())[:_MAX_OUTPUT_CHARS]


class CloseTool(BaseTool):
    name = "close"
    description = "Close CRM - sales pipeline"

    def run(self, action: str = "list", **kwargs: Any) -> ToolResult:
        token = self.config.get("token")
        if not token:
            return ToolResult(False, "", "Close token required")

        headers = {"Authorization": f"Token {token}"}

        try:
            if action == "list_leads":
                response = httpx.get(
                    f"{_BASE_URL}/leads",
                    headers=headers,
                    timeout=30,
                    follow_redirects=False,
                )
                return ToolResult(True, _bounded_response(response))

            if action == "create_lead":
                response = httpx.post(
                    f"{_BASE_URL}/leads",
                    headers=headers,
                    json=kwargs,
                    timeout=30,
                    follow_redirects=False,
                )
                return ToolResult(True, _bounded_response(response))

            return ToolResult(False, "", f"Unknown: {action}")
        except (httpx.HTTPError, ValueError) as exc:
            return ToolResult(False, "", str(exc))


def run(action: str = "list", **kwargs: Any) -> ToolResult:
    """Run the Close CRM tool through the default tool instance."""
    return CloseTool().run(action, **kwargs)
