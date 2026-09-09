"""Safe Calendly API integration."""

from __future__ import annotations

import os
import re
from typing import Any
from urllib.parse import urlsplit

import httpx

from tools.base import ToolResult


PLUGIN_NAME = "calendly"
PLUGIN_DESCRIPTION = "Calendly meeting scheduling"
_MAX_OUTPUT_CHARS = 2000
_USER_PATH_RE = re.compile(r"/users/[A-Za-z0-9-]{1,128}")


def _calendly_user_uri(value: object) -> str:
    """Validate a Calendly user URI before including it as an API parameter."""
    uri = str(value or "").strip()
    parsed = urlsplit(uri)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "api.calendly.com"
        or parsed.username is not None
        or parsed.password is not None
        or not _USER_PATH_RE.fullmatch(parsed.path)
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("user must be a canonical https://api.calendly.com/users/{id} URI.")
    return uri


def _result(response: httpx.Response) -> ToolResult:
    """Serialize a Calendly response within the agent output budget."""
    return ToolResult(response.status_code == 200, str(response.json())[:_MAX_OUTPUT_CHARS])


def _get(url: str, headers: dict[str, str], params: dict[str, Any] | None = None) -> httpx.Response:
    return httpx.get(url, headers=headers, params=params, timeout=30, follow_redirects=False)


def run(action: str = "list", **kwargs: Any) -> ToolResult:
    """Execute supported Calendly read operations."""
    token = os.getenv("CALENDLY_API_TOKEN")
    if not token:
        return ToolResult(False, "", "Calendly token required. Set CALENDLY_API_TOKEN environment variable.")

    headers = {"Authorization": f"Bearer {token}"}

    try:
        if action == "list_events":
            user_uri = kwargs.get("user", os.getenv("CALENDLY_USER_URI"))
            params: dict[str, Any] = {}
            if user_uri:
                params["user"] = _calendly_user_uri(user_uri)
            return _result(_get("https://api.calendly.com/scheduled_events", headers, params))

        if action == "get_user":
            return _result(_get("https://api.calendly.com/users/me", headers))

        if action == "list_event_types":
            user_uri = kwargs.get("user", os.getenv("CALENDLY_USER_URI"))
            if not user_uri:
                return ToolResult(False, "", "user (URI) required for list_event_types or set CALENDLY_USER_URI")
            return _result(
                _get(
                    "https://api.calendly.com/event_types",
                    headers,
                    {"user": _calendly_user_uri(user_uri)},
                )
            )

        return ToolResult(False, "", "Unknown action: {}. Available: list_events, get_user, list_event_types".format(action))
    except (httpx.HTTPError, ValueError) as exc:
        return ToolResult(False, "", str(exc))
