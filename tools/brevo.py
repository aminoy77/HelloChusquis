from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class BrevoTool(Tool):
    name = "brevo"
    description = "Brevo (Sendinblue) - email marketing and SMS"

    def run(self, action: str, **kwargs) -> ToolResult:
        api_key = self.config.get("api_key")
        if not api_key:
            return ToolResult(success=False, error="Brevo API key not configured")

        base_url = "https://api.brevo.com/v3"
        headers = {"api-key": api_key, "Content-Type": "application/json"}

        try:
            if action == "send_email":
                to = kwargs.get("to")
                subject = kwargs.get("subject")
                html = kwargs.get("html", "")

                if not to or not subject:
                    return ToolResult(success=False, error="to and subject required")

                payload = {
                    "sender": {"email": "noreply@example.com"},
                    "to": [{"email": to}],
                    "subject": subject,
                    "htmlContent": html
                }

                r = httpx.post(f"{base_url}/smtp/email", headers=headers, json=payload, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "list_contacts":
                r = httpx.get(f"{base_url}/contacts", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("contacts", []))

            elif action == "create_contact":
                email = kwargs.get("email")
                if not email:
                    return ToolResult(success=False, error="Email required")
                payload = {"email": email, "attributes": kwargs.get("attributes", {})}
                r = httpx.post(f"{base_url}/contacts", headers=headers, json=payload, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "list_campaigns":
                r = httpx.get(f"{base_url}/emailCampaigns", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("campaigns", []))

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))