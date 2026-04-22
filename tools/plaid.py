from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class PlaidTool(Tool):
    name = "plaid"
    description = "Plaid - banking and financial data"

    def run(self, action: str, **kwargs) -> ToolResult:
        client_id = self.config.get("client_id")
        secret = self.config.get("secret")
        env = self.config.get("env", "sandbox")

        if not client_id or not secret:
            return ToolResult(success=False, error="Plaid credentials not configured")

        base_url = f"https://{env}.plaid.com"
        headers = {"Content-Type": "application/json"}

        try:
            if action == "create_link_token":
                payload = {"client_id": client_id, "secret": secret, "client_name": "HelloChusquis", "country_codes": ["US"], "language": "en"}
                r = httpx.post(f"{base_url}/link/token/create", headers=headers, json=payload, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "exchange_token":
                public_token = kwargs.get("public_token")
                if not public_token:
                    return ToolResult(success=False, error="Public token required")
                payload = {"client_id": client_id, "secret": secret, "public_token": public_token}
                r = httpx.post(f"{base_url}/item/public_token/exchange", headers=headers, json=payload, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "get_transactions":
                access_token = kwargs.get("access_token")
                if not access_token:
                    return ToolResult(success=False, error="Access token required")
                payload = {"client_id": client_id, "secret": secret, "access_token": access_token, "start_date": "2024-01-01", "end_date": "2024-12-31"}
                r = httpx.post(f"{base_url}/transactions/get", headers=headers, json=payload, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "get_balance":
                access_token = kwargs.get("access_token")
                if not access_token:
                    return ToolResult(success=False, error="Access token required")
                payload = {"client_id": client_id, "secret": secret, "access_token": access_token}
                r = httpx.post(f"{base_url}/accounts/balance/get", headers=headers, json=payload, timeout=30)
                return ToolResult(success=True, data=r.json())

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))