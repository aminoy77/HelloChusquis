from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class ClerkTool(Tool):
    name = "clerk"
    description = "Clerk - authentication and user management"

    def run(self, action: str, **kwargs) -> ToolResult:
        secret_key = self.config.get("secret_key")
        if not secret_key:
            return ToolResult(success=False, error="Clerk secret key not configured")

        base_url = "https://api.clerk.com/v1"
        headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"}

        try:
            if action == "list_users":
                r = httpx.get(f"{base_url}/users", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("data", []))

            elif action == "get_user":
                id = kwargs.get("id")
                if not id:
                    return ToolResult(success=False, error="User ID required")
                r = httpx.get(f"{base_url}/users/{id}", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "create_user":
                email = kwargs.get("email")
                password = kwargs.get("password")
                if not email or not password:
                    return ToolResult(success=False, error="email and password required")
                payload = {"email_addresses": [email], "password": password}
                r = httpx.post(f"{base_url}/users", headers=headers, json=payload, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "list_organizations":
                r = httpx.get(f"{base_url}/organizations", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("data", []))

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))