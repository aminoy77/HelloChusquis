from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class IntercomTool(Tool):
    name = "intercom"
    description = "Intercom customer messaging and support"

    def run(self, action: str, **kwargs) -> ToolResult:
        token = self.config.get("token")
        if not token:
            return ToolResult(success=False, error="Intercom token not configured")

        base_url = "https://api.intercom.io"
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

        try:
            if action == "list_conversations":
                r = httpx.get(f"{base_url}/conversations", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("conversations", []))

            elif action == "get_conversation":
                id = kwargs.get("id")
                if not id:
                    return ToolResult(success=False, error="Conversation ID required")
                r = httpx.get(f"{base_url}/conversations/{id}", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "list_contacts":
                r = httpx.get(f"{base_url}/contacts", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("data", []))

            elif action == "send_message":
                user_id = kwargs.get("user_id")
                message = kwargs.get("message")
                if not user_id or not message:
                    return ToolResult(success=False, error="user_id and message required")
                payload = {
                    "message_type": "comment",
                    "type": "user",
                    "user_id": user_id,
                    "body": message
                }
                r = httpx.post(f"{base_url}/conversations", headers=headers, json=payload, timeout=30)
                return ToolResult(success=True, data=r.json())

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))