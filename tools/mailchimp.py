from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class MailchimpTool(Tool):
    name = "mailchimp"
    description = "Mailchimp email marketing and automation"

    def run(self, action: str, **kwargs) -> ToolResult:
        api_key = self.config.get("api_key")
        if not api_key:
            return ToolResult(success=False, error="Mailchimp API key not configured")

        dc = api_key.split("-")[-1]
        base_url = f"https://{dc}.api.mailchimp.com/3.0"
        auth = ("anystring", api_key)

        try:
            if action == "list_campaigns":
                r = httpx.get(f"{base_url}/campaigns", auth=auth, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("campaigns", []))

            elif action == "create_campaign":
                subject = kwargs.get("subject")
                if not subject:
                    return ToolResult(success=False, error="Subject required")
                payload = {"type": "regular", "recipients": {"list_id": kwargs.get("list_id", "")}, "settings": {"subject_line": subject}}
                r = httpx.post(f"{base_url}/campaigns", auth=auth, json=payload, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "send_campaign":
                id = kwargs.get("id")
                if not id:
                    return ToolResult(success=False, error="Campaign ID required")
                r = httpx.post(f"{base_url}/campaigns/{id}/actions/send", auth=auth, timeout=30)
                return ToolResult(success=True, data={"sent": True})

            elif action == "list_lists":
                r = httpx.get(f"{base_url}/lists", auth=auth, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("lists", []))

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))