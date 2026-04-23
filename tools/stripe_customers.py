from httpx import AsyncClient


async def create_customer(email: str, name: str, api_key: str) -> dict:
    """Create Stripe customer."""
    url = "https://api.stripe.com/v1/customers"
    async with AsyncClient() as client:
        r = await client.post(url, json={"email": email, "name": name}, auth=(api_key, ""))
        return r.json()


async def get_customer(customer_id: str, api_key: str) -> dict:
    """Get Stripe customer."""
    url = f"https://api.stripe.com/v1/customers/{customer_id}"
    async with AsyncClient() as client:
        r = await client.get(url, auth=(api_key, ""))
        return r.json()


async def list_customers(api_key: str, limit: int = 10) -> dict:
    """List Stripe customers."""
    url = f"https://api.stripe.com/v1/customers?limit={limit}"
    async with AsyncClient() as client:
        r = await client.get(url, auth=(api_key, ""))
        return r.json()


async def create_payment_intent(amount: int, currency: str, api_key: str, **kwargs) -> dict:
    """Create Stripe payment intent."""
    url = "https://api.stripe.com/v1/payment_intents"
    async with AsyncClient() as client:
        r = await client.post(url, json={"amount": amount, "currency": currency, **kwargs}, auth=(api_key, ""))
        return r.json()


async def get_payment_intent(payment_intent_id: str, api_key: str) -> dict:
    """Get Stripe payment intent."""
    url = f"https://api.stripe.com/v1/payment_intents/{payment_intent_id}"
    async with AsyncClient() as client:
        r = await client.get(url, auth=(api_key, ""))
        return r.json()