"""Safe Jotform API integration."""

from __future__ import annotations

import re
from typing import Any

import httpx

from tools.base import BaseTool, ToolResult


_BASE_URL = "https://api.jotform.com"
_FORM_ID_RE = re.compile(r"[1-9][0-9]{0,18}")
_MAX_OUTPUT_CHARS = 2000


def _form_id(value: object) -> str:
    """Validate a Jotform numeric form identifier before embedding it in a path."""
    identifier = str(value or "").strip()
    if not _FORM_ID_RE.fullmatch(identifier):
        raise ValueError("form_id must be a positive numeric identifier.")
    return identifier


def _result(response: httpx.Response) -> ToolResult:
    """Serialize a remote response within the agent output budget."""
    return ToolResult(response.is_success, str(response.json())[:_MAX_OUTPUT_CHARS])


class JotformTool(BaseTool):
    name = "jotform"
    description = "Jotform - online forms"

    def run(self, action: str = "list", **kwargs: Any) -> ToolResult:
        token = self.config.get("token")
        if not token:
            return ToolResult(False, "", "Jotform token required")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        try:
            if action == "list_forms":
                response = httpx.get(
                    f"{_BASE_URL}/user/forms",
                    headers=headers,
                    timeout=30,
                    follow_redirects=False,
                )
                return _result(response)

            if action == "get_submissions":
                response = httpx.get(
                    f"{_BASE_URL}/form/{_form_id(kwargs.get('form_id'))}/submissions",
                    headers=headers,
                    timeout=30,
                    follow_redirects=False,
                )
                return _result(response)

            return ToolResult(False, "", f"Unknown: {action}")
        except (httpx.HTTPError, ValueError) as exc:
            return ToolResult(False, "", str(exc))


def run(action: str = "list", **kwargs: Any) -> ToolResult:
    """Run Jotform through the default tool instance."""
    return JotformTool().run(action, **kwargs)
