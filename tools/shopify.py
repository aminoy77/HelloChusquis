from httpx import AsyncClient


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