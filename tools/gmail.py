"""Gmail integration with safe MIME construction and bounded requests."""

from __future__ import annotations

import base64
import os
import re
from email.message import EmailMessage
from email.utils import getaddresses

import httpx

PLUGIN_NAME = "gmail"
PLUGIN_DESCRIPTION = "Send emails and manage Gmail"
MAX_GMAIL_RESULTS = 100
MAX_GMAIL_RECIPIENTS = 50
MAX_GMAIL_BODY_CHARS = 262_144
MAX_GMAIL_SUBJECT_CHARS = 998
MAX_GMAIL_QUERY_CHARS = 2_048
_MESSAGE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,255}$")
_EMAIL_RE = re.compile(r"^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$")

GMAIL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "gmail",
        "description": "Send emails and manage Gmail messages",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["send_email", "list_emails", "get_email", "search_emails", "get_labels"]},
                "to": {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string", "description": "Email subject"},
                "body": {"type": "string", "description": "Email body content"},
                "cc": {"type": "string", "description": "CC recipients (comma separated)"},
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "number", "description": "Number of results (default 10)"},
                "label": {"type": "string", "description": "Label name or ID"},
            },
            "required": ["action"],
        },
    },
}


def get_gmail_credentials() -> str:
    """Get Gmail OAuth token from environment."""
    return os.getenv("GMAIL_OAUTH_TOKEN") or os.getenv("GMAIL_TOKEN") or ""


def _no_header_controls(value: object, field: str, maximum: int) -> str:
    text = str(value or "")
    if "\r" in text or "\n" in text or "\x00" in text or len(text) > maximum:
        raise ValueError(f"Invalid Gmail {field}.")
    return text


def _recipients(value: object, field: str) -> list[str]:
    raw = _no_header_controls(value, field, MAX_GMAIL_BODY_CHARS)
    addresses = [address for _, address in getaddresses([raw])]
    if not addresses or len(addresses) > MAX_GMAIL_RECIPIENTS or any(not _EMAIL_RE.fullmatch(address) for address in addresses):
        raise ValueError(f"Invalid Gmail {field} recipient list.")
    return addresses


def _bounded_results(value: object) -> int:
    try:
        result_count = int(value)
    except (TypeError, ValueError):
        return 10
    return max(1, min(result_count, MAX_GMAIL_RESULTS))


def _query(value: object, field: str) -> str:
    query = _no_header_controls(value, field, MAX_GMAIL_QUERY_CHARS)
    if not query:
        raise ValueError(f"Gmail {field} is required.")
    return query


def _message_id(value: object) -> str:
    message_id = str(value or "")
    if not _MESSAGE_ID_RE.fullmatch(message_id):
        raise ValueError("Invalid Gmail message ID.")
    return message_id


def encode_email(sender: str, to: str, subject: str, body: str, cc: str = "") -> str:
    """Build and base64url-encode a validated RFC 2822 plain-text email."""
    safe_sender = _recipients(sender, "sender")[0]
    safe_to = _recipients(to, "to")
    safe_subject = _no_header_controls(subject, "subject", MAX_GMAIL_SUBJECT_CHARS)
    safe_body = str(body or "")
    if not safe_subject or not safe_body or len(safe_body) > MAX_GMAIL_BODY_CHARS:
        raise ValueError("Invalid Gmail subject or body.")
    message = EmailMessage()
    message["From"] = safe_sender
    message["To"] = ", ".join(safe_to)
    if cc:
        message["Cc"] = ", ".join(_recipients(cc, "cc"))
    message["Subject"] = safe_subject
    message.set_content(safe_body, charset="utf-8")
    return base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")


def _error(response: httpx.Response) -> str:
    return f"Error: {response.status_code} - {response.text[:200]}"


def run(
    action: str,
    to: str = "",
    subject: str = "",
    body: str = "",
    cc: str = "",
    query: str = "",
    max_results: int = 10,
    label: str = "",
) -> str:
    """Execute bounded Gmail API actions."""
    token = get_gmail_credentials()
    if not token:
        return "Error: Gmail token not found. Set GMAIL_OAUTH_TOKEN."

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    base_url = "https://gmail.googleapis.com/gmail/v1/users/me"
    client = httpx.Client(timeout=30, follow_redirects=False)
    try:
        if action == "get_labels":
            response = client.get(f"{base_url}/labels", headers=headers)
            if response.status_code != 200:
                return _error(response)
            labels = response.json().get("labels", [])[:MAX_GMAIL_RESULTS]
            result = [f"• {item.get('name')} [{item.get('type', 'N/A')}]" for item in labels]
            return "\n".join(result) if result else "No labels found."

        if action == "send_email":
            if not to or not subject or not body:
                return "Error: to, subject, and body required for send_email"
            profile = client.get(f"{base_url}/profile", headers=headers)
            if profile.status_code != 200:
                return "Error: Could not get user profile."
            sender = profile.json().get("emailAddress", "")
            payload = {"raw": encode_email(sender, to, subject, body, cc)}
            response = client.post(f"{base_url}/messages/send", headers=headers, json=payload)
            if response.status_code != 200:
                return _error(response)
            return f"Email sent.\nID: {response.json().get('id')}"

        if action in {"list_emails", "search_emails"}:
            if action == "search_emails":
                search = _query(query, "query")
            elif label:
                search = f"label:{_query(label, 'label')}"
            else:
                search = _query(query or "in:inbox", "query")
            response = client.get(
                f"{base_url}/messages",
                headers=headers,
                params={"maxResults": _bounded_results(max_results), "q": search},
            )
            if response.status_code != 200:
                return _error(response)
            messages = response.json().get("messages", [])[:_bounded_results(max_results)]
            result = [f"• {item.get('id', 'N/A')}" for item in messages]
            return "\n".join(result) if result else "No emails found."

        if action == "get_email":
            response = client.get(f"{base_url}/messages/{_message_id(query)}", headers=headers)
            if response.status_code != 200:
                return _error(response)
            message = response.json()
            header_items = message.get("payload", {}).get("headers", [])
            subject_value = next((item.get("value", "") for item in header_items if item.get("name", "").lower() == "subject"), "No Subject")
            from_addr = next((item.get("value", "") for item in header_items if item.get("name", "").lower() == "from"), "Unknown")
            date = next((item.get("value", "") for item in header_items if item.get("name", "").lower() == "date"), "Unknown")
            return f"From: {from_addr}\nSubject: {subject_value}\nDate: {date}\nID: {message.get('id')}"

        return "Error: Unknown action. Available: send_email, list_emails, get_email, search_emails, get_labels"
    except httpx.TimeoutException:
        return "Error: Request timed out after 30 seconds."
    except (ValueError, httpx.HTTPError) as exc:
        return f"Error: {exc}"
    finally:
        client.close()
