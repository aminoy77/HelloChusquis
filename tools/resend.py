from typing import Optional
from httpx import AsyncClient


async def send_email(key: str, to: str, subject: str, html: str, from_: str) -> dict:
    """Send email via Resend."""
    url = "https://api.resend.com/emails"
    async with AsyncClient() as client:
        r = await client.post(url, json={
            "from": from_,
            "to": [to],
            "subject": subject,
            "html": html
        }, headers={"Authorization": f"Bearer {key}"})
        return r.json()


async def batch_send(key: str, emails: list) -> dict:
    """Batch send emails via Resend."""
    url = "https://api.resend.com/emails/batch"
    async with AsyncClient() as client:
        r = await client.post(url, json=emails, headers={"Authorization": f"Bearer {key}"})
        return r.json()


async def create_template(key: str, name: str, html: str) -> dict:
    """Create Resend template."""
    url = "https://api.resend.com/templates"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name, "html": html}, headers={"Authorization": f"Bearer {key}"})
        return r.json()


async def send_template(key: str, template_id: str, to: str, params: Optional[dict] = None) -> dict:
    """Send template via Resend."""
    if params is None:
        params = {}
    url = f"https://api.resend.com/emails"
    async with AsyncClient() as client:
        r = await client.post(url, json={
            "from": "onboarding@resend.dev",
            "to": [to],
            "subject": "Template",
            "template_id": template_id,
            "params": params
        }, headers={"Authorization": f"Bearer {key}"})
        return r.json()


async def get_domains(key: str) -> dict:
    """Get Resend domains."""
    url = "https://api.resend.com/domains"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {key}"})
        return r.json()