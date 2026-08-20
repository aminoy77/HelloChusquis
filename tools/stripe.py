"""Bounded Stripe invoice integration."""

from __future__ import annotations

import asyncio
import os
import re
from typing import Any

import httpx
from httpx import AsyncClient

STRIPE_HTTP_TIMEOUT_SECONDS = 30
STRIPE_MAX_LIST_LIMIT = 100
STRIPE_MAX_INVOICE_LINES = 100
_INVOICE_ID_RE = re.compile(r"^in_[A-Za-z0-9]+$")


def _client_kwargs() -> dict[str, Any]:
    return {"timeout": STRIPE_HTTP_TIMEOUT_SECONDS, "follow_redirects": False}


def _bounded_limit(value: object) -> int:
    """Normalize Stripe list limits to the provider's safe supported range."""
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return 10
    return max(1, min(limit, STRIPE_MAX_LIST_LIMIT))


def _invoice_id(value: object) -> str:
    """Validate an invoice identifier before it becomes part of a request path."""
    invoice_id = str(value)
    if not _INVOICE_ID_RE.fullmatch(invoice_id):
        raise ValueError("Invalid Stripe invoice ID.")
    return invoice_id


def _invoice_lines(items: object) -> list:
    """Reject oversized or malformed invoice line payloads before transmission."""
    if not isinstance(items, list):
        raise ValueError("Stripe invoice items must be a list.")
    if len(items) > STRIPE_MAX_INVOICE_LINES:
        raise ValueError(f"Stripe invoices support at most {STRIPE_MAX_INVOICE_LINES} line items.")
    return items


async def create_invoice(customer: str, items: list, api_key: str) -> dict:
    """Create a Stripe invoice with a bounded list of invoice lines."""
    async with AsyncClient(**_client_kwargs()) as client:
        response = await client.post(
            "https://api.stripe.com/v1/invoices",
            json={"customer": customer, "lines": _invoice_lines(items)},
            auth=(api_key, ""),
        )
        response.raise_for_status()
        return response.json()


async def get_invoice(invoice_id: str, api_key: str) -> dict:
    """Retrieve a validated Stripe invoice."""
    async with AsyncClient(**_client_kwargs()) as client:
        response = await client.get(
            f"https://api.stripe.com/v1/invoices/{_invoice_id(invoice_id)}",
            auth=(api_key, ""),
        )
        response.raise_for_status()
        return response.json()


async def list_invoices(api_key: str, limit: int = 10) -> dict:
    """List a bounded number of Stripe invoices."""
    async with AsyncClient(**_client_kwargs()) as client:
        response = await client.get(
            "https://api.stripe.com/v1/invoices",
            params={"limit": _bounded_limit(limit)},
            auth=(api_key, ""),
        )
        response.raise_for_status()
        return response.json()


async def finalize_invoice(invoice_id: str, api_key: str) -> dict:
    """Finalize a validated Stripe invoice."""
    async with AsyncClient(**_client_kwargs()) as client:
        response = await client.post(
            f"https://api.stripe.com/v1/invoices/{_invoice_id(invoice_id)}/finalize",
            auth=(api_key, ""),
        )
        response.raise_for_status()
        return response.json()


async def send_invoice(invoice_id: str, api_key: str) -> dict:
    """Send a validated Stripe invoice."""
    async with AsyncClient(**_client_kwargs()) as client:
        response = await client.post(
            f"https://api.stripe.com/v1/invoices/{_invoice_id(invoice_id)}/send",
            auth=(api_key, ""),
        )
        response.raise_for_status()
        return response.json()


def run(action: str, **kwargs) -> str:
    """Synchronous dispatcher for Stripe API actions."""
    api_key = kwargs.get("api_key") or os.getenv("STRIPE_API_KEY")
    if not api_key:
        return "Error: No Stripe API key found. Set STRIPE_API_KEY environment variable."
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return _run_sync(action, api_key, kwargs)
        return loop.run_until_complete(_run_async(action, api_key, kwargs))
    except RuntimeError:
        return _run_sync(action, api_key, kwargs)
    except (httpx.HTTPError, ValueError) as exc:
        return f"Error: {exc}"


async def _run_async(action: str, api_key: str, kwargs: dict) -> str:
    """Async dispatcher for Stripe operations."""
    if action == "create_invoice":
        return str(await create_invoice(kwargs.get("customer", ""), kwargs.get("items", []), api_key))[:2000]
    if action == "get_invoice":
        return str(await get_invoice(kwargs.get("invoice_id", ""), api_key))[:2000]
    if action == "list_invoices":
        return str(await list_invoices(api_key, kwargs.get("limit", 10)))[:2000]
    if action == "finalize_invoice":
        return str(await finalize_invoice(kwargs.get("invoice_id", ""), api_key))[:2000]
    if action == "send_invoice":
        return str(await send_invoice(kwargs.get("invoice_id", ""), api_key))[:2000]
    return "Error: Unknown action. Available: create_invoice, get_invoice, list_invoices, finalize_invoice, send_invoice"


def _response_text(response: httpx.Response) -> str:
    response.raise_for_status()
    return str(response.json())[:2000]


def _run_sync(action: str, api_key: str, kwargs: dict) -> str:
    """Synchronous Stripe dispatcher with a bounded, non-redirecting client."""
    try:
        with httpx.Client(**_client_kwargs()) as client:
            if action == "create_invoice":
                response = client.post(
                    "https://api.stripe.com/v1/invoices",
                    json={"customer": kwargs.get("customer", ""), "lines": _invoice_lines(kwargs.get("items", []))},
                    auth=(api_key, ""),
                )
            elif action == "get_invoice":
                response = client.get(
                    f"https://api.stripe.com/v1/invoices/{_invoice_id(kwargs.get('invoice_id', ''))}",
                    auth=(api_key, ""),
                )
            elif action == "list_invoices":
                response = client.get(
                    "https://api.stripe.com/v1/invoices",
                    params={"limit": _bounded_limit(kwargs.get("limit", 10))},
                    auth=(api_key, ""),
                )
            elif action == "finalize_invoice":
                response = client.post(
                    f"https://api.stripe.com/v1/invoices/{_invoice_id(kwargs.get('invoice_id', ''))}/finalize",
                    auth=(api_key, ""),
                )
            elif action == "send_invoice":
                response = client.post(
                    f"https://api.stripe.com/v1/invoices/{_invoice_id(kwargs.get('invoice_id', ''))}/send",
                    auth=(api_key, ""),
                )
            else:
                return "Error: Unknown action. Available: create_invoice, get_invoice, list_invoices, finalize_invoice, send_invoice"
            return _response_text(response)
    except (httpx.HTTPError, ValueError) as exc:
        return f"Error: {exc}"
