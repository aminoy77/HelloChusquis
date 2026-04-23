from httpx import AsyncClient
import json


async def send_email(domain: str, api_key: str, to: str, subject: str, html: str, from_: str) -> dict:
    """Send email via Mailgun."""
    url = f"https://api.mailgun.net/v3/{domain}/messages"
    async with AsyncClient() as client:
        r = await client.post(url, data={
            "from": from_,
            "to": to,
            "subject": subject,
            "html": html
        }, auth=(f"api", api_key))
        return r.json()


async def send_template(domain: str, api_key: str, to: str, template: str, **kwargs) -> dict:
    """Send template email via Mailgun."""
    url = f"https://api.mailgun.net/v3/{domain}/messages"
    async with AsyncClient() as client:
        r = await client.post(url, data={
            "from": f"@{domain}",
            "to": to,
            "template": template,
            "h:X-Mailgun-Variables": json.dumps(kwargs)
        }, auth=(f"api", api_key))
        return r.json()


async def get_bounces(domain: str, api_key: str, limit: int = 100) -> dict:
    """Get bounces from Mailgun."""
    url = f"https://api.mailgun.net/v3/{domain}/bounces"
    async with AsyncClient() as client:
        r = await client.get(url, params={"limit": limit}, auth=(f"api", api_key))
        return r.json()


async def get_stats(domain: str, api_key: str) -> dict:
    """Get Mailgun stats."""
    url = f"https://api.mailgun.net/v3/{domain}/stats"
    async with AsyncClient() as client:
        r = await client.get(url, auth=(f"api", api_key))
        return r.json()


async def add_to_route(domain: str, api_key: str, expression: str, action: str) -> dict:
    """Add route in Mailgun."""
    url = f"https://api.mailgun.net/v3/{domain}/routes"
    async with AsyncClient() as client:
        r = await client.post(url, data={"expression": expression, "action": action}, auth=(f"api", api_key))
        return r.json()