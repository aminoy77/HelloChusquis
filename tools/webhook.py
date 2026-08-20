"""Outbound webhook tool with SSRF and transport-header protections."""

from __future__ import annotations

import json
from urllib.parse import urlsplit, urlunsplit

import httpx

from tools.web_fetch import SsrFBlockedError, validate_url_safety


PLUGIN_NAME = "webhook"
PLUGIN_DESCRIPTION = "Receive and manage webhooks"

WEBHOOK_SCHEMA = {
    "type": "function",
    "function": {
        "name": "webhook",
        "description": "Create webhook listener or trigger webhooks",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["send", "list"],
                    "description": "Webhook action",
                },
                "url": {"type": "string", "description": "Webhook URL"},
                "payload": {"type": "string", "description": "JSON payload to send"},
                "method": {"type": "string", "description": "HTTP method"},
                "headers": {"type": "string", "description": "Custom headers (JSON)"},
            },
            "required": ["action"],
        },
    },
}

_MAX_PAYLOAD_BYTES = 1_048_576
_MAX_HEADER_BYTES = 16_384
_ALLOWED_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_BLOCKED_HEADER_NAMES = frozenset({
    "connection",
    "content-length",
    "expect",
    "host",
    "keep-alive",
    "proxy-connection",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
})


def _validate_webhook_url(url: str) -> str:
    """Require a public HTTP(S) destination without embedded credentials."""
    try:
        parsed = urlsplit(url.strip())
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid webhook URL") from exc
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("Webhook URL must not include credentials")
    return validate_url_safety(url.strip())


def _public_url(url: str) -> str:
    """Remove query and fragment values that can carry receiver secrets."""
    parsed = urlsplit(url)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


def _parse_headers(raw_headers: str) -> dict[str, str]:
    """Parse caller headers while retaining control of HTTP transport fields."""
    if not raw_headers:
        return {}
    if len(raw_headers.encode("utf-8")) > _MAX_HEADER_BYTES:
        raise ValueError("Webhook headers exceed maximum size")
    try:
        decoded = json.loads(raw_headers)
    except json.JSONDecodeError as exc:
        raise ValueError("Webhook headers must be a JSON object") from exc
    if not isinstance(decoded, dict):
        raise ValueError("Webhook headers must be a JSON object")

    result: dict[str, str] = {}
    for name, value in decoded.items():
        if not isinstance(name, str) or not isinstance(value, str):
            raise ValueError("Webhook headers must contain string names and values")
        normalized = name.lower().strip()
        if normalized in _BLOCKED_HEADER_NAMES:
            raise ValueError(f"Webhook blocked header: {name}")
        if "\r" in name or "\n" in name or "\r" in value or "\n" in value:
            raise ValueError("Webhook headers must not contain newlines")
        result[name] = value
    return result


def run(
    action: str,
    url: str = "",
    payload: str = "{}",
    method: str = "POST",
    headers: str = "",
) -> str:
    """Send an authenticated, policy-gated webhook to a public HTTP(S) endpoint."""
    if action == "send":
        if not url:
            return "Error: url required"
        if len(payload.encode("utf-8")) > _MAX_PAYLOAD_BYTES:
            return "Error: Webhook payload exceeds maximum size"

        try:
            destination = _validate_webhook_url(url)
        except SsrFBlockedError as exc:
            return f"Error: SSRF blocked: {exc}"
        except ValueError as exc:
            return f"Error: {exc}"

        normalized_method = method.upper().strip()
        if normalized_method not in _ALLOWED_METHODS:
            return "Error: Webhook method must be POST, PUT, PATCH, or DELETE"

        try:
            payload_json = json.loads(payload)
        except json.JSONDecodeError:
            payload_json = {"message": payload}

        try:
            header_dict = {"Content-Type": "application/json"}
            header_dict.update(_parse_headers(headers))
        except ValueError as exc:
            return f"Error: {exc}"

        try:
            response = httpx.request(
                normalized_method,
                destination,
                json=payload_json,
                headers=header_dict,
                timeout=30,
                follow_redirects=False,
            )
            return (
                f"Sent to {_public_url(destination)}\n"
                f"Status: {response.status_code}\nResponse: {response.text[:200]}"
            )
        except httpx.HTTPError:
            return "Error: Webhook delivery failed"

    if action == "list":
        return "Webhooks configured in hellochusquis.yaml"
    return f"Error: Unknown action {action}"


if __name__ == "__main__":
    print("Webhook plugin loaded.")
