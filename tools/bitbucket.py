"""Safe Bitbucket Cloud repository and pull-request integration."""

from __future__ import annotations

import os
import re
from typing import Any

import httpx


PLUGIN_NAME = "bitbucket"
PLUGIN_DESCRIPTION = "Bitbucket - Git repositories and pull requests"
_BASE_URL = "https://api.bitbucket.org/2.0"
_SLUG_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}")
_MAX_OUTPUT_CHARS = 2000


def _repo_slug(value: object) -> str:
    """Validate a Bitbucket repository slug before embedding it in a path."""
    slug = str(value or "").strip()
    if not _SLUG_RE.fullmatch(slug):
        raise ValueError("repo must be a single Bitbucket repository slug.")
    return slug


def _workspace(value: object) -> str:
    workspace = str(value or "").strip()
    if not _SLUG_RE.fullmatch(workspace):
        raise ValueError("Bitbucket workspace username must be a single safe slug.")
    return workspace


def _branch(value: object, field_name: str) -> str:
    branch = str(value or "").strip()
    if not branch or len(branch) > 255 or any(char in branch for char in "\r\n\x00"):
        raise ValueError(f"{field_name} must be non-empty, at most 255 characters, and contain no control characters.")
    return branch


def _title(value: object) -> str:
    title = str(value or "").strip()
    if not title or len(title) > 255 or any(char in title for char in "\r\n\x00"):
        raise ValueError("title must be non-empty, at most 255 characters, and contain no control characters.")
    return title


def _fmt(response: httpx.Response, *, values_only: bool = False) -> str:
    """Return a bounded, non-secret representation of a Bitbucket API response."""
    try:
        payload = response.json()
    except ValueError:
        payload = response.text[:_MAX_OUTPUT_CHARS]
    if values_only and isinstance(payload, dict):
        payload = payload.get("values", payload)
    prefix = "" if response.is_success else f"Error {response.status_code}: "
    return prefix + str(payload)[:_MAX_OUTPUT_CHARS]


def _request(method: str, path: str, auth: tuple[str, str], **kwargs: Any) -> httpx.Response:
    return httpx.request(
        method,
        f"{_BASE_URL}{path}",
        auth=auth,
        timeout=30,
        follow_redirects=False,
        **kwargs,
    )


def run(action: str, **kwargs: Any) -> str:
    """Execute safe, bounded Bitbucket repository operations."""
    username = os.getenv("BITBUCKET_USERNAME")
    app_password = os.getenv("BITBUCKET_APP_PASSWORD")
    if not username or not app_password:
        return "Error: Bitbucket credentials not configured. Set BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD environment variables."

    try:
        workspace = _workspace(username)
        auth = (username, app_password)
        if action == "list_repos":
            response = _request("GET", f"/repositories/{workspace}", auth, params={"pagelen": 100})
            return _fmt(response, values_only=True)

        if action == "get_repo":
            response = _request("GET", f"/repositories/{workspace}/{_repo_slug(kwargs.get('repo'))}", auth)
            return _fmt(response)

        if action == "list_pull_requests":
            response = _request(
                "GET",
                f"/repositories/{workspace}/{_repo_slug(kwargs.get('repo'))}/pullrequests",
                auth,
                params={"pagelen": 100},
            )
            return _fmt(response, values_only=True)

        if action == "create_pull_request":
            repo = _repo_slug(kwargs.get("repo"))
            payload = {
                "title": _title(kwargs.get("title")),
                "source": {"branch": {"name": _branch(kwargs.get("source"), "source")}},
                "destination": {"branch": {"name": _branch(kwargs.get("target", "main"), "target")}},
            }
            response = _request("POST", f"/repositories/{workspace}/{repo}/pullrequests", auth, json=payload)
            return _fmt(response)

        return "Error: Unknown action '{}'. Available: list_repos, get_repo, list_pull_requests, create_pull_request".format(action)
    except (httpx.HTTPError, ValueError) as exc:
        return f"Error: {exc}"
