from httpx import AsyncClient


async def send_email(api_key: str, to: str, subject: str, html: str, from_email: str) -> dict:
    """Send email via Brevo (Sendinblue)."""
    url = "https://api.brevo.com/v3/smtp/email"
    async with AsyncClient() as client:
        r = await client.post(url, json={
            "sender": {"email": from_email},
            "to": [{"email": to}],
            "subject": subject,
            "htmlContent": html
        }, headers={"api-key": api_key})
        return r.json()


async def create_template(api_key: str, name: str, html: str, subject: str) -> dict:
    """Create Brevo template."""
    url = "https://api.brevo.com/v3/smtp/templates"
    async with AsyncClient() as client:
        r = await client.post(url, json={
            "name": name,
            "htmlContent": html,
            "subject": subject
        }, headers={"api-key": api_key})
        return r.json()


async def send_template(api_key: str, template_id: int, to: str) -> dict:
    """Send template via Brevo."""
    url = "https://api.brevo.com/v3/smtp/templates/" + str(template_id) + "/send"
    async with AsyncClient() as client:
        r = await client.post(url, json={"email": to}, headers={"api-key": api_key})
        return r.json()


async def get_stats(api_key: str, days: int = 7) -> dict:
    """Get Brevo stats."""
    url = f"https://api.brevo.com/v3/smtp/statistics?days={days}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"api-key": api_key})
        return r.json()


async def import_contacts(api_key: str, contacts: list) -> dict:
    """Import contacts to Brevo."""
    url = "https://api.brevo.com/v3/contacts/import"
    async with AsyncClient() as client:
        r = await client.post(url, json={"contacts": contacts}, headers={"api-key": api_key})
        return r.json()