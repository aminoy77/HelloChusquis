from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class UpstashTool(Tool):
    name = "upstash"
    description = "Upstash - Redis serverless database"

    def run(self, action: str, **kwargs) -> ToolResult:
        email = self.config.get("email")
        token = self.config.get("token")
        if not email or not token:
            return ToolResult(success=False, error="Upstash credentials not configured")

        base_url = "https://us1-console-api.upstash.com"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        try:
            if action == "get":
                key = kwargs.get("key")
                if not key:
                    return ToolResult(success=False, error="Key required")
                r = httpx.get(f"{base_url}/get", headers=headers, params={"key": key}, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "set":
                key = kwargs.get("key")
                value = kwargs.get("value")
                ttl = kwargs.get("ttl", 0)
                if not key or value is None:
                    return ToolResult(success=False, error="key and value required")
                payload = {"key": key, "value": value}
                if ttl:
                    payload["EX"] = ttl
                r = httpx.post(f"{base_url}/set", headers=headers, json=payload, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "incr":
                key = kwargs.get("key")
                if not key:
                    return ToolResult(success=False, error="Key required")
                r = httpx.post(f"{base_url}/incr/{key}", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "del":
                keys = kwargs.get("keys", [])
                if not keys:
                    return ToolResult(success=False, error="Keys required")
                r = httpx.post(f"{base_url}/del", headers=headers, json=keys, timeout=30)
                return ToolResult(success=True, data=r.json())

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))