from httpx import AsyncClient
import os
import httpx


def run(action: str, **kwargs) -> str:
    """Synchronous dispatcher for Shopify API actions."""
    token = kwargs.get("access_token") or os.getenv("SHOPIFY_ACCESS_TOKEN")
    if not token:
        return "Error: No Shopify access token found. Set SHOPIFY_ACCESS_TOKEN environment variable."

    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return _run_sync(action, token, kwargs)
        return loop.run_until_complete(_run_async(action, token, kwargs))
    except RuntimeError:
        return _run_sync(action, token, kwargs)


async def _run_async(action: str, token: str, kwargs: dict) -> str:
    """Async dispatcher for Shopify operations."""
    if action == "create_product":
        return await create_product(kwargs.get("name", ""), kwargs.get("price", 0), kwargs.get("description", ""), token)
    elif action == "get_products":
        return await get_products(token, kwargs.get("limit", 10))
    elif action == "create_order":
        return await create_order(kwargs.get("line_items", []), token)
    elif action == "get_orders":
        return await get_orders(token, kwargs.get("status", "any"), kwargs.get("limit", 10))
    elif action == "update_inventory":
        return await update_inventory(kwargs.get("inventory_item_id", ""), kwargs.get("location_id", ""), kwargs.get("quantity", 0), token)
    else:
        return f"Error: Unknown action '{action}'. Available: create_product, get_products, create_order, get_orders, update_inventory"


def _run_sync(action: str, token: str, kwargs: dict) -> str:
    """Synchronous fallback using httpx.Client."""
    base_url = "https://{shop}.myshopify.com/admin/api/2024-01"
    headers = {"X-Shopify-Access-Token": token}

    try:
        client = httpx.Client(timeout=30)
        if action == "create_product":
            r = client.post(f"{base_url}/products.json", json={"product": {"title": kwargs.get("name", ""), "variants": [{"price": kwargs.get("price", 0)}], "body_html": kwargs.get("description", "")}}, headers=headers)
            return str(r.json())[:2000]
        elif action == "get_products":
            r = client.get(f"{base_url}/products.json", headers=headers)
            return str(r.json())[:2000]
        elif action == "create_order":
            r = client.post(f"{base_url}/orders.json", json={"order": {"line_items": kwargs.get("line_items", [])}}, headers=headers)
            return str(r.json())[:2000]
        elif action == "get_orders":
            status = kwargs.get("status", "any")
            r = client.get(f"{base_url}/orders.json?status={status}", headers=headers)
            return str(r.json())[:2000]
        elif action == "update_inventory":
            r = client.post(f"{base_url}/inventory_levels/set.json", json={"location_id": kwargs.get("location_id", ""), "inventory_item_id": kwargs.get("inventory_item_id", ""), "available": kwargs.get("quantity", 0)}, headers=headers)
            return str(r.json())[:2000]
        else:
            return f"Error: Unknown action '{action}'. Available: create_product, get_products, create_order, get_orders, update_inventory"
    except Exception as e:
        return f"Error: {str(e)}"


async def create_product(name: str, price: float, description: str, access_token: str) -> dict:
    """Create Shopify product."""
    url = "https://{shop}.myshopify.com/admin/api/2024-01/products.json"
    async with AsyncClient() as client:
        r = await client.post(url, json={"product": {"title": name, "variants": [{"price": price}], "body_html": description}}, headers={"X-Shopify-Access-Token": access_token})
        return r.json()


async def get_products(access_token: str, limit: int = 10) -> dict:
    """Get Shopify products."""
    url = "https://{shop}.myshopify.com/admin/api/2024-01/products.json"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"X-Shopify-Access-Token": access_token})
        return r.json()


async def create_order(line_items: list, access_token: str) -> dict:
    """Create Shopify order."""
    url = "https://{shop}.myshopify.com/admin/api/2024-01/orders.json"
    async with AsyncClient() as client:
        r = await client.post(url, json={"order": {"line_items": line_items}}, headers={"X-Shopify-Access-Token": access_token})
        return r.json()


async def get_orders(access_token: str, status: str = "any", limit: int = 10) -> dict:
    """Get Shopify orders."""
    url = f"https://{{shop}}.myshopify.com/admin/api/2024-01/orders.json?status={status}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"X-Shopify-Access-Token": access_token})
        return r.json()


async def update_inventory(inventory_item_id: str, location_id: str, quantity: int, access_token: str) -> dict:
    """Update Shopify inventory."""
    url = f"https://{{shop}}.myshopify.com/admin/api/2024-01/inventory_levels/set.json"
    async with AsyncClient() as client:
        r = await client.post(url, json={"location_id": location_id, "inventory_item_id": inventory_item_id, "available": quantity}, headers={"X-Shopify-Access-Token": access_token})
        return r.json()