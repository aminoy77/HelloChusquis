from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class ShopifyTool(Tool):
    name = "shopify"
    description = "Shopify e-commerce - products, orders, customers"

    def run(self, action: str, **kwargs) -> ToolResult:
        shop = self.config.get("shop")
        token = self.config.get("token")
        if not shop or not token:
            return ToolResult(success=False, error="Shopify credentials not configured")

        base_url = f"https://{shop}.myshopify.com/admin/api/2024-01"
        headers = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}

        try:
            if action == "list_products":
                r = httpx.get(f"{base_url}/products.json", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("products", []))

            elif action == "get_product":
                id = kwargs.get("id")
                if not id:
                    return ToolResult(success=False, error="Product ID required")
                r = httpx.get(f"{base_url}/products/{id}.json", headers=headers, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "list_orders":
                r = httpx.get(f"{base_url}/orders.json", headers=headers, params={"limit": 20}, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("orders", []))

            elif action == "list_customers":
                r = httpx.get(f"{base_url}/customers.json", headers=headers, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("customers", []))

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))