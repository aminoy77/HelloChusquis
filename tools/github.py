from httpx import AsyncClient
import os
import httpx


def run(action: str, **kwargs) -> str:
    """Synchronous dispatcher for GitHub API actions."""
    token = kwargs.get("token") or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if not token:
        return "Error: No GitHub token found. Set GITHUB_TOKEN environment variable."

    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Already inside an async context — use sync httpx instead
            return _run_sync(action, token, kwargs)
        return loop.run_until_complete(_run_async(action, token, kwargs))
    except RuntimeError:
        return _run_sync(action, token, kwargs)


async def _run_async(action: str, token: str, kwargs: dict) -> str:
    """Async dispatcher for GitHub operations."""
    if action == "list_repos":
        return await _async_list_repos(token, kwargs)
    elif action == "get_repo":
        return await _async_get_repo(token, kwargs)
    elif action == "create_repo":
        return await _async_create_repo(token, kwargs)
    elif action == "create_issue":
        return await _async_create_issue(token, kwargs)
    elif action == "list_issues":
        return await _async_list_issues(token, kwargs)
    elif action == "create_release":
        return await _async_create_release(token, kwargs)
    else:
        return f"Error: Unknown action '{action}'. Available: list_repos, get_repo, create_repo, create_issue, list_issues, create_release"


def _run_sync(action: str, token: str, kwargs: dict) -> str:
    """Synchronous fallback using httpx.Client."""
    base_url = "https://api.github.com"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}

    try:
        client = httpx.Client(timeout=30)
        if action == "list_repos":
            r = client.get(f"{base_url}/user/repos", headers=headers)
            return str(r.json())[:2000]
        elif action == "get_repo":
            owner = kwargs.get("owner", "")
            repo = kwargs.get("repo", "")
            r = client.get(f"{base_url}/repos/{owner}/{repo}", headers=headers)
            return str(r.json())[:2000]
        elif action == "create_repo":
            r = client.post(f"{base_url}/user/repos", headers=headers,
                           json={"name": kwargs.get("name", ""), "description": kwargs.get("description", ""), "private": kwargs.get("private", False)})
            return str(r.json())[:2000]
        elif action == "create_issue":
            owner = kwargs.get("owner", "")
            repo = kwargs.get("repo", "")
            r = client.post(f"{base_url}/repos/{owner}/{repo}/issues", headers=headers,
                           json={"title": kwargs.get("title", ""), "body": kwargs.get("body", "")})
            return str(r.json())[:2000]
        elif action == "list_issues":
            owner = kwargs.get("owner", "")
            repo = kwargs.get("repo", "")
            state = kwargs.get("state", "open")
            r = client.get(f"{base_url}/repos/{owner}/{repo}/issues?state={state}", headers=headers)
            return str(r.json())[:2000]
        elif action == "create_release":
            owner = kwargs.get("owner", "")
            repo = kwargs.get("repo", "")
            r = client.post(f"{base_url}/repos/{owner}/{repo}/releases", headers=headers,
                           json={"tag_name": kwargs.get("tag", ""), "name": kwargs.get("name", ""), "body": kwargs.get("body", "")})
            return str(r.json())[:2000]
        else:
            return f"Error: Unknown action '{action}'. Available: list_repos, get_repo, create_repo, create_issue, list_issues, create_release"
    except Exception as e:
        return f"Error: {str(e)}"


# --- Async implementations ---

async def _async_list_repos(token: str, kwargs: dict) -> str:
    url = "https://api.github.com/user/repos"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        return str(r.json())[:2000]


async def _async_get_repo(token: str, kwargs: dict) -> str:
    owner = kwargs.get("owner", "")
    repo = kwargs.get("repo", "")
    url = f"https://api.github.com/repos/{owner}/{repo}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        return str(r.json())[:2000]


async def _async_create_repo(token: str, kwargs: dict) -> str:
    url = "https://api.github.com/user/repos"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": kwargs.get("name", ""), "description": kwargs.get("description", ""), "private": kwargs.get("private", False)}, headers={"Authorization": f"Bearer {token}"})
        return str(r.json())[:2000]


async def _async_create_issue(token: str, kwargs: dict) -> str:
    owner = kwargs.get("owner", "")
    repo = kwargs.get("repo", "")
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    async with AsyncClient() as client:
        r = await client.post(url, json={"title": kwargs.get("title", ""), "body": kwargs.get("body", "")}, headers={"Authorization": f"Bearer {token}"})
        return str(r.json())[:2000]


async def _async_list_issues(token: str, kwargs: dict) -> str:
    owner = kwargs.get("owner", "")
    repo = kwargs.get("repo", "")
    state = kwargs.get("state", "open")
    url = f"https://api.github.com/repos/{owner}/{repo}/issues?state={state}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        return str(r.json())[:2000]


async def _async_create_release(token: str, kwargs: dict) -> str:
    owner = kwargs.get("owner", "")
    repo = kwargs.get("repo", "")
    url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    async with AsyncClient() as client:
        r = await client.post(url, json={"tag_name": kwargs.get("tag", ""), "name": kwargs.get("name", ""), "body": kwargs.get("body", "")}, headers={"Authorization": f"Bearer {token}"})
        return str(r.json())[:2000]


# --- Legacy async API (kept for backward compat) ---


async def create_repo(name: str, description: str, private: bool, token: str) -> dict:
    """Create GitHub repository."""
    url = "https://api.github.com/user/repos"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name, "description": description, "private": private}, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def get_repo(owner: str, repo: str, token: str) -> dict:
    """Get GitHub repository."""
    url = f"https://api.github.com/repos/{owner}/{repo}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def create_issue(owner: str, repo: str, title: str, body: str, token: str) -> dict:
    """Create GitHub issue."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    async with AsyncClient() as client:
        r = await client.post(url, json={"title": title, "body": body}, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def list_issues(owner: str, repo: str, state: str, token: str) -> dict:
    """List GitHub issues."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues?state={state}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def create_release(owner: str, repo: str, tag: str, name: str, body: str, token: str) -> dict:
    """Create GitHub release."""
    url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    async with AsyncClient() as client:
        r = await client.post(url, json={"tag_name": tag, "name": name, "body": body}, headers={"Authorization": f"Bearer {token}"})
        return r.json()