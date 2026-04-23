from httpx import AsyncClient


async def send_email(api_key: str, to: str, subject: str, html: str, from_: str) -> dict:
    """Send email via Postmark."""
    url = "https://api.postmarkapp.com/email"
    async with AsyncClient() as client:
        r = await client.post(url, json={
            "From": from_,
            "To": to,
            "Subject": subject,
            "HtmlBody": html
        }, headers={"X-Postmark-Api-Token": api_key})
        return r.json()


async def batch_send(api_key: str, emails: list) -> dict:
    """Batch send emails via Postmark."""
    url = "https://api.postmarkapp.com/email/batch"
    async with AsyncClient() as client:
        r = await client.post(url, json=emails, headers={"X-Postmark-Api-Token": api_key})
        return r.json()


async def get_deliveries(api_key: str, count: int = 100) -> dict:
    """Get delivery stats from Postmark."""
    url = f"https://api.postmarkapp.com/deliveries?count={count}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"X-Postmark-Api-Token": api_key})
        return r.json()


async def get_bounces(api_key: str, type: str = "hard", count: int = 100) -> dict:
    """Get bounces from Postmark."""
    url = f"https://api.postmarkapp.com/bounces?type={type}&count={count}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"X-Postmark-Api-Token": api_key})
        return r.json()


async def create_template(api_key: str, name: str, subject: str, html: str) -> dict:
    """Create Postmark template."""
    url = "https://api.postmarkapp.com/templates"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name, "subject": subject, "htmlBody": html}, headers={"X-Postmark-Api-Token": api_key})
        return r.json()