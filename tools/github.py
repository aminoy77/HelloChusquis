"""Safe, bounded GitHub API integration."""

from __future__ import annotations

import asyncio
import os
import re
from typing import Any

import httpx
from httpx import AsyncClient

_GITHUB_API = "https://api.github.com"
_GITHUB_TIMEOUT_SECONDS = 30
_GITHUB_MAX_RESULTS = 100
_GITHUB_MAX_NAME_CHARS = 100
_GITHUB_MAX_TITLE_CHARS = 256
_GITHUB_MAX_BODY_CHARS = 65_536
_PATH_SEGMENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")


def _client_kwargs() -> dict[str, Any]:
    return {"timeout": _GITHUB_TIMEOUT_SECONDS, "follow_redirects": False}


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}


def _segment(value: object, label: str) -> str:
    candidate = str(value or "")
    if not _PATH_SEGMENT_RE.fullmatch(candidate):
        raise ValueError(f"Invalid GitHub {label}.")
    return candidate


def _repo_path(kwargs: dict) -> str:
    owner = _segment(kwargs.get("owner"), "owner")
    repository = _segment(kwargs.get("repo"), "repository")
    return f"/repos/{owner}/{repository}"


def _bounded_state(value: object) -> str:
    state = str(value or "open").lower()
    return state if state in {"open", "closed", "all"} else "open"


def _private_value(value: object) -> bool:
    if isinstance(value, str):
        return value.strip().lower() not in {"false", "0", "no", "off"}
    return bool(value)


def _repository_payload(kwargs: dict) -> dict:
    name = _segment(kwargs.get("name"), "repository name")
    description = str(kwargs.get("description", ""))
    if len(description) > _GITHUB_MAX_BODY_CHARS:
        raise ValueError("Repository description exceeds the allowed length.")
    return {"name": name, "description": description, "private": _private_value(kwargs.get("private", True))}


def _issue_payload(kwargs: dict) -> dict:
    title = str(kwargs.get("title", ""))
    body = str(kwargs.get("body", ""))
    if not title or len(title) > _GITHUB_MAX_TITLE_CHARS:
        raise ValueError("GitHub issue title is missing or too long.")
    if len(body) > _GITHUB_MAX_BODY_CHARS:
        raise ValueError("GitHub issue body exceeds the allowed length.")
    return {"title": title, "body": body}


def _release_payload(kwargs: dict) -> dict:
    tag = str(kwargs.get("tag", ""))
    name = str(kwargs.get("name", ""))
    body = str(kwargs.get("body", ""))
    if not tag or len(tag) > _GITHUB_MAX_NAME_CHARS or "\x00" in tag:
        raise ValueError("GitHub release tag is missing or invalid.")
    if len(name) > _GITHUB_MAX_TITLE_CHARS or len(body) > _GITHUB_MAX_BODY_CHARS:
        raise ValueError("GitHub release metadata exceeds the allowed length.")
    return {"tag_name": tag, "name": name, "body": body}


def _response_text(response: httpx.Response) -> str:
    response.raise_for_status()
    return str(response.json())[:2000]


def run(action: str, **kwargs) -> str:
    """Synchronous dispatcher for approved GitHub API actions."""
    token = kwargs.get("token") or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if not token:
        return "Error: No GitHub token found. Set GITHUB_TOKEN environment variable."
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return _run_sync(action, str(token), kwargs)
        return loop.run_until_complete(_run_async(action, str(token), kwargs))
    except RuntimeError:
        return _run_sync(action, str(token), kwargs)
    except (httpx.HTTPError, ValueError) as exc:
        return f"Error: {exc}"


async def _run_async(action: str, token: str, kwargs: dict) -> str:
    """Async dispatcher for bounded GitHub operations."""
    if action == "list_repos":
        return str(await _async_list_repos(token, kwargs))[:2000]
    if action == "get_repo":
        return str(await _async_get_repo(token, kwargs))[:2000]
    if action == "create_repo":
        return str(await _async_create_repo(token, kwargs))[:2000]
    if action == "create_issue":
        return str(await _async_create_issue(token, kwargs))[:2000]
    if action == "list_issues":
        return str(await _async_list_issues(token, kwargs))[:2000]
    if action == "create_release":
        return str(await _async_create_release(token, kwargs))[:2000]
    return "Error: Unknown action. Available: list_repos, get_repo, create_repo, create_issue, list_issues, create_release"


def _run_sync(action: str, token: str, kwargs: dict) -> str:
    """Synchronous GitHub dispatcher with a safe, closed HTTP client."""
    client = httpx.Client(**_client_kwargs())
    try:
        headers = _headers(token)
        if action == "list_repos":
            response = client.get(f"{_GITHUB_API}/user/repos", headers=headers, params={"per_page": _GITHUB_MAX_RESULTS})
        elif action == "get_repo":
            response = client.get(f"{_GITHUB_API}{_repo_path(kwargs)}", headers=headers)
        elif action == "create_repo":
            response = client.post(f"{_GITHUB_API}/user/repos", headers=headers, json=_repository_payload(kwargs))
        elif action == "create_issue":
            response = client.post(f"{_GITHUB_API}{_repo_path(kwargs)}/issues", headers=headers, json=_issue_payload(kwargs))
        elif action == "list_issues":
            response = client.get(
                f"{_GITHUB_API}{_repo_path(kwargs)}/issues",
                headers=headers,
                params={"state": _bounded_state(kwargs.get("state")), "per_page": _GITHUB_MAX_RESULTS},
            )
        elif action == "create_release":
            response = client.post(f"{_GITHUB_API}{_repo_path(kwargs)}/releases", headers=headers, json=_release_payload(kwargs))
        else:
            return "Error: Unknown action. Available: list_repos, get_repo, create_repo, create_issue, list_issues, create_release"
        return _response_text(response)
    except (httpx.HTTPError, ValueError) as exc:
        return f"Error: {exc}"
    finally:
        client.close()


async def _async_request(method: str, path: str, token: str, **kwargs) -> dict:
    """Issue one GitHub request using bounded transport settings."""
    async with AsyncClient(**_client_kwargs()) as client:
        response = await client.request(method, f"{_GITHUB_API}{path}", headers=_headers(token), **kwargs)
        response.raise_for_status()
        return response.json()


async def _async_list_repos(token: str, kwargs: dict) -> dict:
    del kwargs
    return await _async_request("GET", "/user/repos", token, params={"per_page": _GITHUB_MAX_RESULTS})


async def _async_get_repo(token: str, kwargs: dict) -> dict:
    return await _async_request("GET", _repo_path(kwargs), token)


async def _async_create_repo(token: str, kwargs: dict) -> dict:
    return await _async_request("POST", "/user/repos", token, json=_repository_payload(kwargs))


async def _async_create_issue(token: str, kwargs: dict) -> dict:
    return await _async_request("POST", f"{_repo_path(kwargs)}/issues", token, json=_issue_payload(kwargs))


async def _async_list_issues(token: str, kwargs: dict) -> dict:
    return await _async_request(
        "GET",
        f"{_repo_path(kwargs)}/issues",
        token,
        params={"state": _bounded_state(kwargs.get("state")), "per_page": _GITHUB_MAX_RESULTS},
    )


async def _async_create_release(token: str, kwargs: dict) -> dict:
    return await _async_request("POST", f"{_repo_path(kwargs)}/releases", token, json=_release_payload(kwargs))


async def create_repo(name: str, description: str, private: bool = True, token: str = "") -> dict:
    """Create a private-by-default GitHub repository for legacy callers."""
    return await _async_create_repo(token, {"name": name, "description": description, "private": private})


async def get_repo(owner: str, repo: str, token: str) -> dict:
    """Get a GitHub repository for legacy callers."""
    return await _async_get_repo(token, {"owner": owner, "repo": repo})


async def create_issue(owner: str, repo: str, title: str, body: str, token: str) -> dict:
    """Create a GitHub issue for legacy callers."""
    return await _async_create_issue(token, {"owner": owner, "repo": repo, "title": title, "body": body})


async def list_issues(owner: str, repo: str, state: str, token: str) -> dict:
    """List GitHub issues for legacy callers."""
    return await _async_list_issues(token, {"owner": owner, "repo": repo, "state": state})


async def create_release(owner: str, repo: str, tag: str, name: str, body: str, token: str) -> dict:
    """Create a GitHub release for legacy callers."""
    return await _async_create_release(token, {"owner": owner, "repo": repo, "tag": tag, "name": name, "body": body})
