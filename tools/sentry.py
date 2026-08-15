from __future__ import annotations

import os
import httpx

PLUGIN_NAME = "sentry"
PLUGIN_DESCRIPTION = "Sentry error tracking and performance monitoring"


def run(action: str, **kwargs) -> str:
    token = os.getenv("SENTRY_TOKEN")
    org = os.getenv("SENTRY_ORG")
    if not token or not org:
        return "Error: Sentry credentials not configured. Set SENTRY_TOKEN and SENTRY_ORG environment variables."

    base_url = f"https://sentry.io/api/0/organizations/{org}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        if action == "list_issues":
            r = httpx.get(f"{base_url}/issues/", headers=headers, timeout=30)
            data = r.json()
            items = [
                {"id": i.get("id"), "title": i.get("title"), "level": i.get("level"), "status": i.get("status")}
                for i in data[:20]
            ]
            return str(items)

        elif action == "get_issue":
            issue_id = kwargs.get("id")
            if not issue_id:
                return "Error: Issue ID required for get_issue"
            r = httpx.get(f"{base_url}/issues/{issue_id}/", headers=headers, timeout=30)
            return _fmt(r)

        elif action == "list_projects":
            r = httpx.get(f"{base_url}/projects/", headers=headers, timeout=30)
            data = r.json()
            return str([
                {"id": p.get("id"), "name": p.get("name"), "slug": p.get("slug")}
                for p in data
            ])

        elif action == "get_stats":
            id = kwargs.get("id")
            if not id:
                return "Error: Project ID required for get_stats"
            r = httpx.get(f"{base_url}/projects/{id}/stats/", headers=headers, params={"stat": "all"}, timeout=30)
            return _fmt(r)

        else:
            return f"Error: Unknown action '{action}'. Available: list_issues, get_issue, list_projects, get_stats"
    except httpx.TimeoutException:
        return "Error: Request timed out after 30 seconds."
    except Exception as e:
        return f"Error: {e}"


def _fmt(r: httpx.Response) -> str:
    try:
        return str(r.json())
    except Exception:
        return r.text[:500]