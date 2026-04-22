from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class SendGridTool(Tool):
    name = "sendgrid"
    description = "SendGrid transactional email and marketing"

    def run(self, action: str, **kwargs) -> ToolResult:
        api_key = self.config.get("api_key")
        from_email = self.config.get("from_email", "noreply@example.com")

        if not api_key:
            return ToolResult(success=False, error="SendGrid API key not configured")

        base_url = "https://api.sendgrid.com/v3"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        try:
            if action == "send_email":
                to = kwargs.get("to")
                subject = kwargs.get("subject")
                content = kwargs.get("content")
                html = kwargs.get("html", content)

                if not to or not subject or not content:
                    return ToolResult(success=False, error="Missing required fields")

                payload = {
                    "personalizations": [{"to": [{"email": to}]}],
                    "from": {"email": from_email},
                    "subject": subject,
                    "content": [
                        {"type": "text/plain", "value": content},
                        {"type": "text/html", "value": html}
                    ]
                }

                r = httpx.post(f"{base_url}/mail/send", headers=headers, json=payload, timeout=30)
                return ToolResult(success=True, data={"status": r.status_code})

            elif action == "list_contacts":
                r = httpx.get(f"{base_url}/marketing/contacts", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "get_stats":
                r = httpx.get(f"{base_url}/stats/global", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))