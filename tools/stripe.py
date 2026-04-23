from httpx import AsyncClient


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


async def send_invoice(invoice_id: str, api_key: str) -> dict:
    """Send Stripe invoice."""
    url = f"https://api.stripe.com/v1/invoices/{invoice_id}/send"
    async with AsyncClient() as client:
        r = await client.post(url, auth=(api_key, ""))
        return r.json()