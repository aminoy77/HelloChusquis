from typing import Optional
from httpx import AsyncClient
import os
import re
import httpx

_MAX_RESEND_BATCH = 100
_EMAIL_RE = re.compile(r"^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$")


def _recipient(value: object) -> str:
    recipient = str(value or "")
    if "\r" in recipient or "\n" in recipient or not _EMAIL_RE.fullmatch(recipient):
        raise ValueError("Invalid Resend recipient.")
    return recipient


def _bounded_batch(value: object) -> list:
    if not isinstance(value, list) or not value or len(value) > _MAX_RESEND_BATCH:
        raise ValueError(f"Resend batch must contain 1 to {_MAX_RESEND_BATCH} emails.")
    return value


def run(action: str, **kwargs) -> str:
    """Synchronous dispatcher for Resend API actions."""
    key = kwargs.get("key") or os.getenv("RESEND_API_KEY")
    if not key:
        return "Error: No Resend API key found. Set RESEND_API_KEY environment variable."

    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return _run_sync(action, key, kwargs)
        return loop.run_until_complete(_run_async(action, key, kwargs))
    except RuntimeError:
        return _run_sync(action, key, kwargs)


async def _run_async(action: str, key: str, kwargs: dict) -> str:
    """Async dispatcher for Resend operations."""
    if action == "send_email":
        return await send_email(key, kwargs.get("to", ""), kwargs.get("subject", ""), kwargs.get("html", ""), kwargs.get("from_", ""))
    elif action == "batch_send":
        return await batch_send(key, kwargs.get("emails", []))
    elif action == "create_template":
        return await create_template(key, kwargs.get("name", ""), kwargs.get("html", ""))
    elif action == "send_template":
        return await send_template(key, kwargs.get("template_id", ""), kwargs.get("to", ""), kwargs.get("params"))
    elif action == "get_domains":
        return await get_domains(key)
    else:
        return f"Error: Unknown action '{action}'. Available: send_email, batch_send, create_template, send_template, get_domains"


def _run_sync(action: str, key: str, kwargs: dict) -> str:
    """Synchronous fallback using httpx.Client."""
    base_url = "https://api.resend.com"
    headers = {"Authorization": f"Bearer {key}"}

    try:
        client = httpx.Client(timeout=30)
        if action == "send_email":
            r = client.post(f"{base_url}/emails", json={"from": kwargs.get("from_", ""), "to": [_recipient(kwargs.get("to", ""))], "subject": kwargs.get("subject", ""), "html": kwargs.get("html", "")}, headers=headers)
            return str(r.json())[:2000]
        elif action == "batch_send":
            r = client.post(f"{base_url}/emails/batch", json=_bounded_batch(kwargs.get("emails", [])), headers=headers)
            return str(r.json())[:2000]
        elif action == "create_template":
            r = client.post(f"{base_url}/templates", json={"name": kwargs.get("name", ""), "html": kwargs.get("html", "")}, headers=headers)
            return str(r.json())[:2000]
        elif action == "send_template":
            r = client.post(f"{base_url}/emails", json={"from": "onboarding@resend.dev", "to": [kwargs.get("to", "")], "subject": "Template", "template_id": kwargs.get("template_id", ""), "params": kwargs.get("params", {})}, headers=headers)
            return str(r.json())[:2000]
        elif action == "get_domains":
            r = client.get(f"{base_url}/domains", headers=headers)
            return str(r.json())[:2000]
        else:
            return f"Error: Unknown action '{action}'. Available: send_email, batch_send, create_template, send_template, get_domains"
    except Exception as e:
        return f"Error: {str(e)}"


async def send_email(key: str, to: str, subject: str, html: str, from_: str) -> dict:
    """Send email via Resend."""
    url = "https://api.resend.com/emails"
    async with AsyncClient() as client:
        r = await client.post(url, json={
            "from": from_,
            "to": [_recipient(to)],
            "subject": subject,
            "html": html
        }, headers={"Authorization": f"Bearer {key}"})
        return r.json()


async def batch_send(key: str, emails: list) -> dict:
    """Batch send emails via Resend."""
    url = "https://api.resend.com/emails/batch"
    async with AsyncClient() as client:
        r = await client.post(url, json=_bounded_batch(emails), headers={"Authorization": f"Bearer {key}"})
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
    url = "https://api.resend.com/emails"
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