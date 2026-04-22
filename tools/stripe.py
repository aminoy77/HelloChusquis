from __future__ import annotations

import httpx
import json
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class StripeTool(Tool):
    name = "stripe"
    description = "Stripe payment processing - customers, charges, subscriptions, invoices"

    def run(self, action: str, **kwargs) -> ToolResult:
        api_key = self.config.get("api_key")
        if not api_key:
            return ToolResult(success=False, error="Stripe API key not configured")

        base_url = "https://api.stripe.com/v1"
        headers = {"Authorization": f"Bearer {api_key}"}

        try:
            if action == "list_customers":
                r = httpx.get(f"{base_url}/customers", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=[
                    {"id": c.get("id"), "email": c.get("email"), "name": c.get("name")}
                    for c in data.get("data", [])
                ])

            elif action == "create_customer":
                r = httpx.post(f"{base_url}/customers", headers=headers, data=kwargs, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "create_charge":
                r = httpx.post(f"{base_url}/charges", headers=headers, data=kwargs, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "list_invoices":
                r = httpx.get(f"{base_url}/invoices", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("data", []))

            elif action == "list_subscriptions":
                r = httpx.get(f"{base_url}/subscriptions", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("data", []))

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))