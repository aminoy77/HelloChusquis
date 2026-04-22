from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class TwilioTool(Tool):
    name = "twilio"
    description = "Twilio SMS, voice calls, and messaging"

    def run(self, action: str, **kwargs) -> ToolResult:
        account_sid = self.config.get("account_sid")
        auth_token = self.config.get("auth_token")
        from_number = self.config.get("from_number")

        if not account_sid or not auth_token:
            return ToolResult(success=False, error="Twilio credentials not configured")

        base_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}"
        auth = (account_sid, auth_token)

        try:
            if action == "send_sms":
                to = kwargs.get("to")
                message = kwargs.get("message")
                if not to or not message:
                    return ToolResult(success=False, error="Missing 'to' or 'message'")

                r = httpx.post(
                    f"{base_url}/Messages.json",
                    auth=auth,
                    data={"To": to, "From": from_number, "Body": message},
                    timeout=30
                )
                return ToolResult(success=True, data=r.json())

            elif action == "list_messages":
                r = httpx.get(f"{base_url}/Messages.json", auth=auth, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=[
                    {"sid": m.get("sid"), "to": m.get("to"), "body": m.get("body"), "date": m.get("date_sent")}
                    for m in data.get("messages", [])
                ])

            elif action == "make_call":
                to = kwargs.get("to")
                url = kwargs.get("url")
                if not to:
                    return ToolResult(success=False, error="Missing 'to'")

                r = httpx.post(
                    f"{base_url}/Calls.json",
                    auth=auth,
                    data={"To": to, "From": from_number, "Twiml": f"<Response><Say>{url or 'Hello'}</Say></Response>"},
                    timeout=30
                )
                return ToolResult(success=True, data=r.json())

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))