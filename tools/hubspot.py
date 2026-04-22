from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class HubSpotTool(Tool):
    name = "hubspot"
    description = "HubSpot CRM - contacts, deals, companies"

    def run(self, action: str, **kwargs) -> ToolResult:
        token = self.config.get("token")
        if not token:
            return ToolResult(success=False, error="HubSpot token not configured")

        base_url = "https://api.hubapi.com"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        try:
            if action == "list_contacts":
                r = httpx.get(f"{base_url}/crm/v3/objects/contacts", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("results", []))

            elif action == "create_contact":
                email = kwargs.get("email")
                first_name = kwargs.get("first_name", "")
                last_name = kwargs.get("last_name", "")
                if not email:
                    return ToolResult(success=False, error="Email required")
                payload = {"properties": {"email": email, "firstname": first_name, "lastname": last_name}}
                r = httpx.post(f"{base_url}/crm/v3/objects/contacts", headers=headers, json=payload, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "list_deals":
                r = httpx.get(f"{base_url}/crm/v3/objects/deals", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("results", []))

            elif action == "list_companies":
                r = httpx.get(f"{base_url}/crm/v3/objects/companies", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("results", []))

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))