"""Safe Typeform API integration."""

from __future__ import annotations

import re
from typing import Any

import httpx

from tools.base import BaseTool, ToolResult


_BASE_URL = "https://api.typeform.com"
_FORM_ID_RE = re.compile(r"[A-Za-z0-9_-]{1,128}")
_MAX_OUTPUT_CHARS = 2000


def _form_id(value: object) -> str:
    """Validate a Typeform form identifier before embedding it in an API path."""
    identifier = str(value or "").strip()
    if not _FORM_ID_RE.fullmatch(identifier):
        raise ValueError("form_id must be a single safe path segment.")
    return identifier


def _result(response: httpx.Response) -> ToolResult:
    """Serialize a remote response within the agent output budget."""
    return ToolResult(response.is_success, str(response.json())[:_MAX_OUTPUT_CHARS])


class TypeformTool(BaseTool):
    name = "typeform"
    description = "Typeform - forms and surveys"

    def run(self, action: str = "list", **kwargs: Any) -> ToolResult:
        token = self.config.get("token")
        if not token:
            return ToolResult(False, "", "Typeform token required")

        headers = {"Authorization": f"Bearer {token}"}

        try:
            if action == "list_forms":
                response = httpx.get(
                    f"{_BASE_URL}/forms",
                    headers=headers,
                    timeout=30,
                    follow_redirects=False,
                )
                return _result(response)

            if action == "get_responses":
                response = httpx.get(
                    f"{_BASE_URL}/forms/{_form_id(kwargs.get('form_id'))}/responses",
                    headers=headers,
                    timeout=30,
                    follow_redirects=False,
                )
                return _result(response)

            return ToolResult(False, "", f"Unknown: {action}")
        except (httpx.HTTPError, ValueError) as exc:
            return ToolResult(False, "", str(exc))


def run(action: str = "list", **kwargs: Any) -> ToolResult:
    """Run Typeform through the default tool instance."""
    return TypeformTool().run(action, **kwargs)
