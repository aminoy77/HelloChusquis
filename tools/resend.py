from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class ResendTool(Tool):
    name = "resend"
    description = "Resend - modern email delivery"

    def run(self, action: str, **kwargs) -> ToolResult:
        api_key = self.config.get("api_key")
        from_email = self.config.get("from_email", "noreply@example.com")

        if not api_key:
            return ToolResult(success=False, error="Resend API key not configured")

        base_url = "https://api.resend.com"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        try:
            if action == "send":
                to = kwargs.get("to")
                subject = kwargs.get("subject")
                html = kwargs.get("html", "")
                text = kwargs.get("text", "")

                if not to or not subject:
                    return ToolResult(success=False, error="to and subject required")

                payload = {
                    "from": from_email,
                    "to": [to],
                    "subject": subject,
                    "html": html,
                    "text": text
                }

                r = httpx.post(f"{base_url}/email", headers=headers, json=payload, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "batch":
                emails = kwargs.get("emails", [])
                if not emails:
                    return ToolResult(success=False, error="Emails array required")
                r = httpx.post(f"{base_url}/emails/batch", headers=headers, json={"emails": emails}, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "list":
                r = httpx.get(f"{base_url}/emails", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("data", []))

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))