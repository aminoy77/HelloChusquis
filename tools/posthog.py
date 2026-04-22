from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class PostHogTool(Tool):
    name = "posthog"
    description = "PostHog - product analytics and feature flags"

    def run(self, action: str, **kwargs) -> ToolResult:
        api_key = self.config.get("api_key")
        if not api_key:
            return ToolResult(success=False, error="PostHog API key not configured")

        base_url = "https://app.posthog.com"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        try:
            if action == "capture":
                event = kwargs.get("event")
                properties = kwargs.get("properties", {})
                if not event:
                    return ToolResult(success=False, error="Event name required")
                payload = {"event": event, "properties": properties, "timestamp": kwargs.get("timestamp", "")}
                r = httpx.post(f"{base_url}/capture", headers=headers, json=payload, timeout=30)
                return ToolResult(success=True, data={"captured": True})

            elif action == "list_feature_flags":
                r = httpx.get(f"{base_url}/api/feature_flags", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("results", []))

            elif action == "get_flag":
                key = kwargs.get("key")
                distinct_id = kwargs.get("distinct_id")
                if not key or not distinct_id:
                    return ToolResult(success=False, error="key and distinct_id required")
                r = httpx.get(f"{base_url}/api/feature_flags/eval", headers=headers, params={"key": key, "distinct_id": distinct_id}, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "list_insights":
                r = httpx.get(f"{base_url}/api/insights", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("results", []))

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))