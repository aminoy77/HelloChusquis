"""Twilio integration with validated account endpoints."""

from __future__ import annotations

import os
import re

import httpx

_TWILIO_BASE = "https://api.twilio.com/2010-04-01"
_ACCOUNT_SID_RE = re.compile(r"^AC[a-fA-F0-9]{32}$")


def _account_sid(value: object) -> str:
    sid = str(value or "")
    if not _ACCOUNT_SID_RE.fullmatch(sid):
        raise ValueError("Invalid Twilio account SID.")
    return sid


def _phone(value: object) -> str:
    phone = str(value or "")
    if not re.fullmatch(r"\+[1-9][0-9]{7,14}", phone):
        raise ValueError("Twilio phone numbers must use E.164 format.")
    return phone


def _message(value: object) -> str:
    message = str(value or "")
    if not message or len(message) > 1_600:
        raise ValueError("Twilio message must contain 1 to 1600 characters.")
    return message


def _response_text(response: httpx.Response) -> str:
    response.raise_for_status()
    return str(response.json())[:2000]


def run(action: str, **kwargs) -> str:
    """Execute validated Twilio operations through the current account."""
    auth_token = kwargs.get("auth") or os.getenv("TWILIO_AUTH_TOKEN")
    account_sid = kwargs.get("account_sid") or os.getenv("TWILIO_ACCOUNT_SID")
    if not auth_token or not account_sid:
        return "Error: Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN."
    try:
        return _run_sync(action, _account_sid(account_sid), str(auth_token), kwargs)
    except (httpx.HTTPError, ValueError) as exc:
        return f"Error: {exc}"


def _run_sync(action: str, account_sid: str, auth_token: str, kwargs: dict) -> str:
    """Run a bounded Twilio request with HTTP Basic authentication."""
    base_url = f"{_TWILIO_BASE}/Accounts/{account_sid}"
    auth = (account_sid, auth_token)
    client = httpx.Client(timeout=30, follow_redirects=False)
    try:
        if action == "send_message":
            response = client.post(
                f"{base_url}/Messages.json",
                data={"To": _phone(kwargs.get("to")), "Body": _message(kwargs.get("message"))},
                auth=auth,
            )
        elif action == "list_messages":
            params = {"To": _phone(kwargs["to"])} if kwargs.get("to") else {"PageSize": 100}
            response = client.get(f"{base_url}/Messages.json", params=params, auth=auth)
        elif action == "get_call_log":
            call_sid = str(kwargs.get("sid", ""))
            if not re.fullmatch(r"^CA[a-fA-F0-9]{32}$", call_sid):
                raise ValueError("Invalid Twilio call SID.")
            response = client.get(f"{base_url}/Calls/{call_sid}.json", auth=auth)
        else:
            return "Error: Unknown action. Available: send_message, list_messages, get_call_log"
        return _response_text(response)
    finally:
        client.close()
