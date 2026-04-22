from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class SquareTool(Tool):
    name = "square"
    description = "Square payments, orders, and catalog"

    def run(self, action: str, **kwargs) -> ToolResult:
        token = self.config.get("token")
        location_id = self.config.get("location_id")
        if not token:
            return ToolResult(success=False, error="Square token not configured")

        base_url = "https://connect.squareup.com/v2"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        try:
            if action == "list_payments":
                r = httpx.get(f"{base_url}/payments", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("payments", []))

            elif action == "create_payment":
                amount = kwargs.get("amount")
                currency = kwargs.get("currency", "USD")
                if not amount:
                    return ToolResult(success=False, error="Amount required")
                source_id = kwargs.get("source_id", "cnon:card-nonce-ok")
                payload = {"source_id": source_id, "idempotency_key": kwargs.get("idempotency_key", ""), "amount_money": {"amount": int(amount * 100), "currency": currency}}
                if location_id:
                    payload["location_id"] = location_id
                r = httpx.post(f"{base_url}/payments", headers=headers, json=payload, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "list_orders":
                r = httpx.get(f"{base_url}/orders", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("orders", []))

            elif action == "list_locations":
                r = httpx.get(f"{base_url}/locations", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("locations", []))

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))