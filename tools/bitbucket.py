from __future__ import annotations

import os
import httpx

PLUGIN_NAME = "bitbucket"
PLUGIN_DESCRIPTION = "Bitbucket - Git repositories and pull requests"


def run(action: str, **kwargs) -> str:
    username = os.getenv("BITBUCKET_USERNAME")
    app_password = os.getenv("BITBUCKET_APP_PASSWORD")
    if not username or not app_password:
        return "Error: Bitbucket credentials not configured. Set BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD environment variables."

    base_url = "https://api.bitbucket.org/2.0"
    auth = (username, app_password)

    try:
        if action == "list_repos":
            r = httpx.get(f"{base_url}/repositories/{username}", auth=auth, timeout=30)
            data = r.json()
            return str(data.get("values", data))

        elif action == "get_repo":
            repo = kwargs.get("repo")
            if not repo:
                return "Error: repo required for get_repo"
            r = httpx.get(f"{base_url}/repositories/{username}/{repo}", auth=auth, timeout=30)
            return _fmt(r)

        elif action == "list_pull_requests":
            repo = kwargs.get("repo")
            if not repo:
                return "Error: repo required for list_pull_requests"
            r = httpx.get(f"{base_url}/repositories/{username}/{repo}/pullrequests", auth=auth, timeout=30)
            data = r.json()
            return str(data.get("values", data))

        elif action == "create_pull_request":
            repo = kwargs.get("repo")
            title = kwargs.get("title")
            source = kwargs.get("source")
            if not repo or not title or not source:
                return "Error: repo, title, and source required for create_pull_request"
            target = kwargs.get("target", "main")
            payload = {
                "title": title,
                "source": {"branch": {"name": source}},
                "destination": {"branch": {"name": target}},
            }
            r = httpx.post(f"{base_url}/repositories/{username}/{repo}/pullrequests", auth=auth, json=payload, timeout=30)
            return _fmt(r)

        else:
            return f"Error: Unknown action '{action}'. Available: list_repos, get_repo, list_pull_requests, create_pull_request"
    except httpx.TimeoutException:
        return "Error: Request timed out after 30 seconds."
    except Exception as e:
        return f"Error: {e}"


def _fmt(r: httpx.Response) -> str:
    try:
        return str(r.json())
    except Exception:
        return r.text[:500]