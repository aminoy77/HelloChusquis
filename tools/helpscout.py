"""Safe Help Scout API integration."""

from __future__ import annotations

import re
from typing import Any

from httpx import AsyncClient


_BASE_URL = "https://api.helpscout.net/v2"
_ID_RE = re.compile(r"[1-9][0-9]{0,18}")
_EMAIL_RE = re.compile(
    r"[A-Za-z0-9.!#$%&'*+=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+"
)
_THREAD_TYPES = frozenset({"customer", "reply", "note", "chat", "phone"})
_CONVERSATION_STATUSES = frozenset({"active", "pending", "closed", "spam"})


def _helpscout_id(value: object, field_name: str) -> str:
    """Validate a Help Scout numeric identifier before embedding it in a path."""
    identifier = str(value or "").strip()
    if not _ID_RE.fullmatch(identifier):
        raise ValueError(f"{field_name} must be a positive numeric identifier.")
    return identifier


def _email(value: object) -> str:
    email = str(value or "").strip()
    if len(email) > 254 or not _EMAIL_RE.fullmatch(email):
        raise ValueError("A valid customer email is required.")
    return email


def _bounded_text(value: object, field_name: str, maximum: int) -> str:
    text = str(value or "")
    if not text.strip() or len(text) > maximum or "\x00" in text:
        raise ValueError(f"{field_name} must be non-empty, within {maximum} characters, and contain no null bytes.")
    return text


def _thread_type(value: object) -> str:
    thread_type = str(value or "customer").strip().lower()
    if thread_type not in _THREAD_TYPES:
        raise ValueError("type must be one of: customer, reply, note, chat, phone.")
    return thread_type


def _conversation_status(value: object) -> str:
    status = str(value or "").strip().lower()
    if status not in _CONVERSATION_STATUSES:
        raise ValueError("status must be one of: active, pending, closed, spam.")
    return status


def _headers(auth: str) -> dict[str, str]:
    return {"Authorization": auth}


async def _request(
    method: str,
    path: str,
    auth: str,
    *,
    json: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Perform one bounded Help Scout API request without following redirects."""
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.request(
            method,
            f"{_BASE_URL}{path}",
            json=json,
            headers=_headers(auth),
        )
        return response.json()


async def create_ticket(
    email: str,
    subject: str,
    body: str,
    auth: str,
    mailbox_id: int = 1,
) -> dict[str, Any]:
    """Create a Help Scout conversation in a validated mailbox."""
    return await _request(
        "POST",
        "/conversations",
        auth,
        json={
            "customer": {"email": _email(email)},
            "subject": _bounded_text(subject, "subject", 500),
            "mailbox": {"id": int(_helpscout_id(mailbox_id, "mailbox_id"))},
            "threads": [{"type": "customer", "body": _bounded_text(body, "body", 65_535)}],
        },
    )


async def list_conversations(auth: str, mailbox: int = 1) -> dict[str, Any]:
    """List conversations in a validated mailbox."""
    return await _request(
        "GET",
        f"/mailboxes/{_helpscout_id(mailbox, 'mailbox_id')}/conversations",
        auth,
    )


async def get_conversation(auth: str, conversation_id: int) -> dict[str, Any]:
    """Get a conversation selected by a validated identifier."""
    return await _request(
        "GET",
        f"/conversations/{_helpscout_id(conversation_id, 'conversation_id')}",
        auth,
    )


async def add_thread(auth: str, conversation_id: int, body: str, type: str = "customer") -> dict[str, Any]:
    """Add a bounded thread of an allowed type to a validated conversation."""
    return await _request(
        "POST",
        f"/conversations/{_helpscout_id(conversation_id, 'conversation_id')}/threads",
        auth,
        json={"type": _thread_type(type), "body": _bounded_text(body, "body", 65_535)},
    )


async def update_ticket_status(auth: str, conversation_id: int, status: str) -> dict[str, Any]:
    """Update a validated conversation with an allowed state transition value."""
    return await _request(
        "PATCH",
        f"/conversations/{_helpscout_id(conversation_id, 'conversation_id')}",
        auth,
        json={"status": _conversation_status(status)},
    )
