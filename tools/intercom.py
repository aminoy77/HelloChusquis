"""Safe Intercom API integration."""

from __future__ import annotations

import asyncio
import os
import re
from typing import Any

import httpx


_BASE_URL = "https://api.intercom.io"
_CONVERSATION_ID_RE = re.compile(r"[A-Za-z0-9_-]{1,128}")
_CONVERSATION_STATES = frozenset({"open", "closed", "snoozed"})
_MESSAGE_TYPES = frozenset({"comment", "note"})


def _conversation_id(value: object) -> str:
    """Validate a conversation identifier before embedding it in an API path."""
    identifier = str(value or "").strip()
    if not _CONVERSATION_ID_RE.fullmatch(identifier):
        raise ValueError("conversation_id must be a single safe identifier.")
    return identifier


def _conversation_state(value: object) -> str:
    state = str(value or "open").strip().lower()
    if state not in _CONVERSATION_STATES:
        raise ValueError("state must be one of: open, closed, snoozed.")
    return state


def _message_type(value: object) -> str:
    message_type = str(value or "comment").strip().lower()
    if message_type not in _MESSAGE_TYPES:
        raise ValueError("message_type must be either comment or note.")
    return message_type


def _clean_fields(kwargs: dict[str, Any], *excluded: str) -> dict[str, Any]:
    blocked = {"action", "token", *excluded}
    return {key: value for key, value in kwargs.items() if key not in blocked}


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}


async def _request(
    method: str,
    path: str,
    token: str,
    *,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Perform a redirect-free Intercom request with an explicit timeout."""
    async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.request(
            method,
            f"{_BASE_URL}{path}",
            json=json,
            params=params,
            headers=_headers(token),
        )
        return response.json()


def run(action: str, **kwargs: Any) -> str:
    """Synchronous dispatcher for Intercom API actions."""
    token = kwargs.get("token") or os.getenv("INTERCOM_ACCESS_TOKEN")
    if not token:
        return "Error: No Intercom token found. Set INTERCOM_ACCESS_TOKEN environment variable."

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        try:
            return asyncio.run(_run_async(action, str(token), kwargs))
        except (ValueError, httpx.HTTPError) as exc:
            return f"Error: {exc}"
    return _run_sync(action, str(token), kwargs)


async def _run_async(action: str, token: str, kwargs: dict[str, Any]) -> str:
    """Async dispatcher for Intercom operations."""
    if action == "create_conversation":
        result = await create_conversation(
            token,
            kwargs.get("from_", ""),
            kwargs.get("body", ""),
            **_clean_fields(kwargs, "from_", "body"),
        )
    elif action == "list_conversations":
        result = await list_conversations(token, kwargs.get("state", "open"))
    elif action == "get_conversation":
        result = await get_conversation(token, kwargs.get("conversation_id", ""))
    elif action == "reply_conversation":
        result = await reply_conversation(
            token,
            kwargs.get("conversation_id", ""),
            kwargs.get("message_type", "comment"),
            kwargs.get("body", ""),
        )
    elif action == "update_conversation":
        result = await update_conversation(
            token,
            kwargs.get("conversation_id", ""),
            **_clean_fields(kwargs, "conversation_id"),
        )
    else:
        return "Error: Unknown action '{}'. Available: create_conversation, list_conversations, get_conversation, reply_conversation, update_conversation".format(action)
    return str(result)[:2000]


def _run_sync(action: str, token: str, kwargs: dict[str, Any]) -> str:
    """Synchronous fallback that remains safe when an event loop is active."""
    try:
        with httpx.Client(timeout=30, follow_redirects=False) as client:
            if action == "create_conversation":
                response = client.post(
                    f"{_BASE_URL}/conversations",
                    json={
                        "from": {"type": "user", "email": kwargs.get("from_", "")},
                        "body": kwargs.get("body", ""),
                        **_clean_fields(kwargs, "from_", "body"),
                    },
                    headers=_headers(token),
                )
            elif action == "list_conversations":
                response = client.get(
                    f"{_BASE_URL}/conversations",
                    headers=_headers(token),
                    params={"state": _conversation_state(kwargs.get("state", "open"))},
                )
            elif action == "get_conversation":
                response = client.get(
                    f"{_BASE_URL}/conversations/{_conversation_id(kwargs.get('conversation_id', ''))}",
                    headers=_headers(token),
                )
            elif action == "reply_conversation":
                response = client.post(
                    f"{_BASE_URL}/conversations/{_conversation_id(kwargs.get('conversation_id', ''))}/reply",
                    json={
                        "message_type": _message_type(kwargs.get("message_type", "comment")),
                        "type": "user",
                        "body": str(kwargs.get("body", ""))[:65535],
                    },
                    headers=_headers(token),
                )
            elif action == "update_conversation":
                response = client.put(
                    f"{_BASE_URL}/conversations/{_conversation_id(kwargs.get('conversation_id', ''))}",
                    json=_clean_fields(kwargs, "conversation_id"),
                    headers=_headers(token),
                )
            else:
                return "Error: Unknown action '{}'. Available: create_conversation, list_conversations, get_conversation, reply_conversation, update_conversation".format(action)
            return str(response.json())[:2000]
    except (ValueError, httpx.HTTPError) as exc:
        return f"Error: {exc}"


async def create_conversation(token: str, from_: str, body: str, **kwargs: Any) -> dict[str, Any]:
    """Create an Intercom conversation with explicitly separated metadata."""
    return await _request(
        "POST",
        "/conversations",
        token,
        json={
            "from": {"type": "user", "email": from_},
            "body": str(body or "")[:65535],
            **_clean_fields(kwargs, "from_", "body"),
        },
    )


async def list_conversations(token: str, state: str = "open") -> dict[str, Any]:
    """List conversations using a constrained state filter."""
    return await _request(
        "GET",
        "/conversations",
        token,
        params={"state": _conversation_state(state)},
    )


async def get_conversation(token: str, conversation_id: str) -> dict[str, Any]:
    """Get a single conversation selected by a safe identifier."""
    return await _request("GET", f"/conversations/{_conversation_id(conversation_id)}", token)


async def reply_conversation(
    token: str,
    conversation_id: str,
    message_type: str,
    body: str,
) -> dict[str, Any]:
    """Reply to a conversation with a constrained message type."""
    return await _request(
        "POST",
        f"/conversations/{_conversation_id(conversation_id)}/reply",
        token,
        json={
            "message_type": _message_type(message_type),
            "type": "user",
            "body": str(body or "")[:65535],
        },
    )


async def update_conversation(token: str, conversation_id: str, **kwargs: Any) -> dict[str, Any]:
    """Update a conversation selected by a validated identifier."""
    return await _request(
        "PUT",
        f"/conversations/{_conversation_id(conversation_id)}",
        token,
        json=_clean_fields(kwargs, "conversation_id"),
    )
