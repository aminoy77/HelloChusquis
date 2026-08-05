from httpx import AsyncClient
import os
import httpx


async def create_invoice(customer: str, items: list, api_key: str) -> dict:
    """Create Stripe invoice."""
    url = "https://api.stripe.com/v1/invoices"
    async with AsyncClient() as client:
        r = await client.post(url, json={"customer": customer, "lines": items}, auth=(api_key, ""))
        return r.json()


async def get_invoice(invoice_id: str, api_key: str) -> dict:
    """Get Stripe invoice."""
    url = f"https://api.stripe.com/v1/invoices/{invoice_id}"
    async with AsyncClient() as client:
        r = await client.get(url, auth=(api_key, ""))
        return r.json()


async def list_invoices(api_key: str, limit: int = 10) -> dict:
    """List Stripe invoices."""
    url = f"https://api.stripe.com/v1/invoices?limit={limit}"
    async with AsyncClient() as client:
        r = await client.get(url, auth=(api_key, ""))
        return r.json()


async def finalize_invoice(invoice_id: str, api_key: str) -> dict:
    """Finalize Stripe invoice."""
    url = f"https://api.stripe.com/v1/invoices/{invoice_id}/finalize"
    async with AsyncClient() as client:
        r = await client.post(url, auth=(api_key, ""))
        return r.json()


def run(action: str, **kwargs) -> str:
    """Synchronous dispatcher for Stripe API actions."""
    api_key = kwargs.get("api_key") or os.getenv("STRIPE_API_KEY")
    if not api_key:
        return "Error: No Stripe API key found. Set STRIPE_API_KEY environment variable."
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return _run_sync(action, api_key, kwargs)
        return loop.run_until_complete(_run_async(action, api_key, kwargs))
    except RuntimeError:
        return _run_sync(action, api_key, kwargs)


async def _run_async(action: str, api_key: str, kwargs: dict) -> str:
    """Async dispatcher for Stripe operations."""
    if action == "create_invoice":
        return str(await create_invoice(kwargs.get("customer", ""), kwargs.get("items", []), api_key))
    elif action == "get_invoice":
        return str(await get_invoice(kwargs.get("invoice_id", ""), api_key))
    elif action == "list_invoices":
        return str(await list_invoices(api_key, kwargs.get("limit", 10)))
    elif action == "finalize_invoice":
        return str(await finalize_invoice(kwargs.get("invoice_id", ""), api_key))
    elif action == "send_invoice":
        return str(await send_invoice(kwargs.get("invoice_id", ""), api_key))
    else:
        return f"Error: Unknown action '{action}'. Available: create_invoice, get_invoice, list_invoices, finalize_invoice, send_invoice"


def _run_sync(action: str, api_key: str, kwargs: dict) -> str:
    """Synchronous fallback using httpx.Client."""
    try:
        client = httpx.Client(timeout=30)
        if action == "create_invoice":
            r = client.post("https://api.stripe.com/v1/invoices",
                           json={"customer": kwargs.get("customer", ""), "lines": kwargs.get("items", [])},
                           auth=(api_key, ""))
            return str(r.json())[:2000]
        elif action == "get_invoice":
            r = client.get(f"https://api.stripe.com/v1/invoices/{kwargs.get('invoice_id', '')}", auth=(api_key, ""))
            return str(r.json())[:2000]
        elif action == "list_invoices":
            r = client.get(f"https://api.stripe.com/v1/invoices?limit={kwargs.get('limit', 10)}", auth=(api_key, ""))
            return str(r.json())[:2000]
        elif action == "finalize_invoice":
            r = client.post(f"https://api.stripe.com/v1/invoices/{kwargs.get('invoice_id', '')}/finalize", auth=(api_key, ""))
            return str(r.json())[:2000]
        elif action == "send_invoice":
            r = client.post(f"https://api.stripe.com/v1/invoices/{kwargs.get('invoice_id', '')}/send", auth=(api_key, ""))
            return str(r.json())[:2000]
        else:
            return f"Error: Unknown action '{action}'. Available: create_invoice, get_invoice, list_invoices, finalize_invoice, send_invoice"
    except Exception as e:
        return f"Error: {str(e)}"


async def send_invoice(invoice_id: str, api_key: str) -> dict:
    """Send Stripe invoice."""
    url = f"https://api.stripe.com/v1/invoices/{invoice_id}/send"
    async with AsyncClient() as client:
        r = await client.post(url, auth=(api_key, ""))
        return r.json()