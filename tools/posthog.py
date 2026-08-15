from __future__ import annotations

import os
import httpx

PLUGIN_NAME = "posthog"
PLUGIN_DESCRIPTION = "PostHog - product analytics and feature flags"


def run(action: str, **kwargs) -> str:
    api_key = os.getenv("POSTHOG_API_KEY")
    project_id = os.getenv("POSTHOG_PROJECT_ID", "")
    if not api_key:
        return "Error: No PostHog API key found. Set POSTHOG_API_KEY environment variable."

    base_url = "https://app.posthog.com"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        if action == "capture":
            event = kwargs.get("event")
            if not event:
                return "Error: event name required for capture"
            payload = {
                "api_key": api_key,
                "event": event,
                "properties": kwargs.get("properties", {}) or {},
                "timestamp": kwargs.get("timestamp", ""),
            }
            r = httpx.post(f"{base_url}/capture", headers=headers, json=payload, timeout=30)
            return f"Event '{event}' captured (status {r.status_code})"

        elif action == "list_feature_flags":
            r = httpx.get(f"{base_url}/api/projects/{project_id}/feature_flags/" if project_id else f"{base_url}/api/feature_flags", headers=headers, timeout=30)
            data = r.json()
            return str(data.get("results", data))

        elif action == "get_flag":
            key = kwargs.get("key")
            distinct_id = kwargs.get("distinct_id")
            if not key or not distinct_id:
                return "Error: key and distinct_id required for get_flag"
            r = httpx.get(
                f"{base_url}/api/feature_flags/eval",
                headers=headers,
                params={"key": key, "distinct_id": distinct_id},
                timeout=30,
            )
            return _fmt(r)

        elif action == "list_insights":
            r = httpx.get(f"{base_url}/api/insights", headers=headers, timeout=30)
            data = r.json()
            return str(data.get("results", data))

        else:
            return f"Error: Unknown action '{action}'. Available: capture, list_feature_flags, get_flag, list_insights"
    except httpx.TimeoutException:
        return "Error: Request timed out after 30 seconds."
    except Exception as e:
        return f"Error: {e}"


def _fmt(r: httpx.Response) -> str:
    try:
        return str(r.json())
    except Exception:
        return r.text[:500]