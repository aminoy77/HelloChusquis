"""Safe Shopify Admin API integration."""

from __future__ import annotations

import asyncio
import os
import re
from typing import Any

import httpx


_SHOP_DOMAIN_RE = re.compile(
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.myshopify\.com"
)
_SHOPIFY_API_VERSION = "2024-01"
_SHOPIFY_STATUSES = frozenset({"any", "open", "closed", "cancelled"})


def _shopify_base_url(shop: object) -> str:
    """Return the fixed Shopify Admin API origin for a canonical store domain."""
    store_domain = str(shop or "").strip().lower()
    if not _SHOP_DOMAIN_RE.fullmatch(store_domain):
        raise ValueError("SHOPIFY_SHOP must be a canonical *.myshopify.com domain.")
    return f"https://{store_domain}/admin/api/{_SHOPIFY_API_VERSION}"


def _shopify_base_url_from_kwargs(kwargs: dict[str, Any]) -> str:
    return _shopify_base_url(kwargs.get("shop") or os.getenv("SHOPIFY_SHOP"))


def _bounded_limit(value: object, default: int = 10) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError):
        limit = default
    return max(1, min(limit, 250))


def _positive_integer(value: object, field_name: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a positive integer.") from exc
    if number <= 0 or isinstance(value, bool):
        raise ValueError(f"{field_name} must be a positive integer.")
    return number


def run(action: str, **kwargs: Any) -> str:
    """Synchronous dispatcher for Shopify API actions."""
    token = kwargs.get("access_token") or os.getenv("SHOPIFY_ACCESS_TOKEN")
    if not token:
        return "Error: No Shopify access token found. Set SHOPIFY_ACCESS_TOKEN environment variable."
    try:
        base_url = _shopify_base_url_from_kwargs(kwargs)
    except ValueError as exc:
        return f"Error: {exc}"

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return _run_sync(action, str(token), kwargs, base_url)
        return loop.run_until_complete(_run_async(action, str(token), kwargs, base_url))
    except RuntimeError:
        return _run_sync(action, str(token), kwargs, base_url)


async def _run_async(action: str, token: str, kwargs: dict[str, Any], base_url: str) -> str:
    """Async dispatcher for Shopify operations."""
    if action == "create_product":
        result = await create_product(
            kwargs.get("name", ""),
            kwargs.get("price", 0),
            kwargs.get("description", ""),
            token,
            base_url=base_url,
        )
    elif action == "get_products":
        result = await get_products(token, kwargs.get("limit", 10), base_url=base_url)
    elif action == "create_order":
        result = await create_order(kwargs.get("line_items", []), token, base_url=base_url)
    elif action == "get_orders":
        result = await get_orders(
            token,
            kwargs.get("status", "any"),
            kwargs.get("limit", 10),
            base_url=base_url,
        )
    elif action == "update_inventory":
        result = await update_inventory(
            kwargs.get("inventory_item_id", ""),
            kwargs.get("location_id", ""),
            kwargs.get("quantity", 0),
            token,
            base_url=base_url,
        )
    else:
        return "Error: Unknown action '{}'. Available: create_product, get_products, create_order, get_orders, update_inventory".format(action)
    return str(result)[:2000]


def _run_sync(action: str, token: str, kwargs: dict[str, Any], base_url: str) -> str:
    """Synchronous fallback using a bounded, redirect-free HTTP client."""
    headers = {"X-Shopify-Access-Token": token}
    try:
        with httpx.Client(timeout=30, follow_redirects=False) as client:
            if action == "create_product":
                response = client.post(
                    f"{base_url}/products.json",
                    json={
                        "product": {
                            "title": kwargs.get("name", ""),
                            "variants": [{"price": kwargs.get("price", 0)}],
                            "body_html": kwargs.get("description", ""),
                        }
                    },
                    headers=headers,
                )
            elif action == "get_products":
                response = client.get(
                    f"{base_url}/products.json",
                    headers=headers,
                    params={"limit": _bounded_limit(kwargs.get("limit", 10))},
                )
            elif action == "create_order":
                response = client.post(
                    f"{base_url}/orders.json",
                    json={"order": {"line_items": _line_items(kwargs.get("line_items", []))}},
                    headers=headers,
                )
            elif action == "get_orders":
                response = client.get(
                    f"{base_url}/orders.json",
                    headers=headers,
                    params={
                        "status": _shopify_status(kwargs.get("status", "any")),
                        "limit": _bounded_limit(kwargs.get("limit", 10)),
                    },
                )
            elif action == "update_inventory":
                response = client.post(
                    f"{base_url}/inventory_levels/set.json",
                    json={
                        "location_id": _positive_integer(kwargs.get("location_id", ""), "location_id"),
                        "inventory_item_id": _positive_integer(kwargs.get("inventory_item_id", ""), "inventory_item_id"),
                        "available": _inventory_quantity(kwargs.get("quantity", 0)),
                    },
                    headers=headers,
                )
            else:
                return "Error: Unknown action '{}'. Available: create_product, get_products, create_order, get_orders, update_inventory".format(action)
            return str(response.json())[:2000]
    except (httpx.HTTPError, ValueError) as exc:
        return f"Error: {exc}"


def _line_items(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValueError("line_items must be a non-empty list.")
    if len(value) > 250 or any(not isinstance(item, dict) for item in value):
        raise ValueError("line_items must contain at most 250 objects.")
    return value


def _shopify_status(value: object) -> str:
    status = str(value or "any").strip().lower()
    if status not in _SHOPIFY_STATUSES:
        raise ValueError("status must be one of: any, open, closed, cancelled.")
    return status


def _inventory_quantity(value: object) -> int:
    try:
        quantity = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("quantity must be an integer.") from exc
    if isinstance(value, bool):
        raise ValueError("quantity must be an integer.")
    return quantity


async def _request(
    method: str,
    path: str,
    access_token: str,
    *,
    base_url: str | None = None,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    url = f"{base_url or _shopify_base_url(os.getenv('SHOPIFY_SHOP'))}{path}"
    async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.request(
            method,
            url,
            json=json,
            params=params,
            headers={"X-Shopify-Access-Token": access_token},
        )
        return response.json()


async def create_product(
    name: str,
    price: float,
    description: str,
    access_token: str,
    *,
    base_url: str | None = None,
) -> dict[str, Any]:
    """Create a Shopify product in the selected store."""
    return await _request(
        "POST",
        "/products.json",
        access_token,
        base_url=base_url,
        json={"product": {"title": name, "variants": [{"price": price}], "body_html": description}},
    )


async def get_products(
    access_token: str,
    limit: int = 10,
    *,
    base_url: str | None = None,
) -> dict[str, Any]:
    """Return a bounded list of Shopify products."""
    return await _request(
        "GET",
        "/products.json",
        access_token,
        base_url=base_url,
        params={"limit": _bounded_limit(limit)},
    )


async def create_order(
    line_items: list[dict[str, Any]],
    access_token: str,
    *,
    base_url: str | None = None,
) -> dict[str, Any]:
    """Create a Shopify order with a bounded set of line items."""
    return await _request(
        "POST",
        "/orders.json",
        access_token,
        base_url=base_url,
        json={"order": {"line_items": _line_items(line_items)}},
    )


async def get_orders(
    access_token: str,
    status: str = "any",
    limit: int = 10,
    *,
    base_url: str | None = None,
) -> dict[str, Any]:
    """Return bounded Shopify orders filtered by a valid status."""
    return await _request(
        "GET",
        "/orders.json",
        access_token,
        base_url=base_url,
        params={"status": _shopify_status(status), "limit": _bounded_limit(limit)},
    )


async def update_inventory(
    inventory_item_id: str,
    location_id: str,
    quantity: int,
    access_token: str,
    *,
    base_url: str | None = None,
) -> dict[str, Any]:
    """Set inventory for validated item and location identifiers."""
    return await _request(
        "POST",
        "/inventory_levels/set.json",
        access_token,
        base_url=base_url,
        json={
            "location_id": _positive_integer(location_id, "location_id"),
            "inventory_item_id": _positive_integer(inventory_item_id, "inventory_item_id"),
            "available": _inventory_quantity(quantity),
        },
    )
