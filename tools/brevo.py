from httpx import AsyncClient
import os
import re
import httpx

_MAX_BREVO_CONTACTS = 1000
_EMAIL_RE = re.compile(r"^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$")


def _email(value: object) -> str:
    email = str(value or "")
    if "\r" in email or "\n" in email or not _EMAIL_RE.fullmatch(email):
        raise ValueError("Invalid Brevo email address.")
    return email


def _contacts(value: object) -> list:
    if not isinstance(value, list) or len(value) > _MAX_BREVO_CONTACTS:
        raise ValueError(f"Brevo contacts must be a list of at most {_MAX_BREVO_CONTACTS} items.")
    return value


def run(action: str, **kwargs) -> str:
    """Synchronous dispatcher for Brevo API actions."""
    api_key = kwargs.get("api_key") or os.getenv("BREVO_API_KEY")
    if not api_key:
        return "Error: No Brevo API key found. Set BREVO_API_KEY environment variable."

    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return _run_sync(action, api_key, kwargs)
        return loop.run_until_complete(_run_async(action, api_key, kwargs))
    except RuntimeError:
        return _run_sync(action, api_key, kwargs)


async def _run_async(action: str, api_key: str, kwargs: dict) -> str:
    """Async dispatcher for Brevo operations."""
    if action == "send_email":
        return await send_email(api_key, kwargs.get("to", ""), kwargs.get("subject", ""), kwargs.get("html", ""), kwargs.get("from_email", ""))
    elif action == "create_template":
        return await create_template(api_key, kwargs.get("name", ""), kwargs.get("html", ""), kwargs.get("subject", ""))
    elif action == "send_template":
        return await send_template(api_key, kwargs.get("template_id", 0), kwargs.get("to", ""))
    elif action == "get_stats":
        return await get_stats(api_key, kwargs.get("days", 7))
    elif action == "import_contacts":
        return await import_contacts(api_key, kwargs.get("contacts", []))
    else:
        return f"Error: Unknown action '{action}'. Available: send_email, create_template, send_template, get_stats, import_contacts"


def _run_sync(action: str, api_key: str, kwargs: dict) -> str:
    """Synchronous fallback using httpx.Client."""
    base_url = "https://api.brevo.com/v3"
    headers = {"api-key": api_key}

    try:
        client = httpx.Client(timeout=30)
        if action == "send_email":
            r = client.post(f"{base_url}/smtp/email", json={"sender": {"email": _email(kwargs.get("from_email", ""))}, "to": [{"email": _email(kwargs.get("to", ""))}], "subject": kwargs.get("subject", ""), "htmlContent": kwargs.get("html", "")}, headers=headers)
            return str(r.json())[:2000]
        elif action == "create_template":
            r = client.post(f"{base_url}/smtp/templates", json={"name": kwargs.get("name", ""), "htmlContent": kwargs.get("html", ""), "subject": kwargs.get("subject", "")}, headers=headers)
            return str(r.json())[:2000]
        elif action == "send_template":
            template_id = kwargs.get("template_id", 0)
            r = client.post(f"{base_url}/smtp/templates/{template_id}/send", json={"email": kwargs.get("to", "")}, headers=headers)
            return str(r.json())[:2000]
        elif action == "get_stats":
            days = kwargs.get("days", 7)
            r = client.get(f"{base_url}/smtp/statistics?days={days}", headers=headers)
            return str(r.json())[:2000]
        elif action == "import_contacts":
            r = client.post(f"{base_url}/contacts/import", json={"contacts": _contacts(kwargs.get("contacts", []))}, headers=headers)
            return str(r.json())[:2000]
        else:
            return f"Error: Unknown action '{action}'. Available: send_email, create_template, send_template, get_stats, import_contacts"
    except Exception as e:
        return f"Error: {str(e)}"


async def send_email(api_key: str, to: str, subject: str, html: str, from_email: str) -> dict:
    """Send email via Brevo (Sendinblue)."""
    url = "https://api.brevo.com/v3/smtp/email"
    async with AsyncClient() as client:
        r = await client.post(url, json={
            "sender": {"email": _email(from_email)},
            "to": [{"email": _email(to)}],
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
        r = await client.post(url, json={"contacts": _contacts(contacts)}, headers={"api-key": api_key})
        return r.json()