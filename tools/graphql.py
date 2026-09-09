"""Safe generic GraphQL client and email drafting helper."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

from tools.web_fetch import validate_url_safety


PLUGIN_NAME = "graphql"
PLUGIN_DESCRIPTION = "Execute GraphQL operations"
_MAX_QUERY_CHARS = 50_000
_MAX_RESPONSE_BYTES = 256 * 1024
_MAX_OUTPUT_CHARS = 2_000

GRAPHQL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "graphql",
        "description": "Execute GraphQL operations",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["query", "mutation", "introspect"]},
                "endpoint": {"type": "string", "description": "GraphQL endpoint URL"},
                "query": {"type": "string", "description": "GraphQL query or mutation"},
                "variables": {"type": "string", "description": "Variables as JSON"},
                "headers": {"type": "string", "description": "Headers as JSON"},
            },
            "required": ["action", "endpoint", "query"],
        },
    },
}


def _safe_endpoint(value: object) -> str:
    """Validate an endpoint through the shared SSRF policy before connecting."""
    endpoint = str(value or "").strip()
    if not endpoint or len(endpoint) > 8192 or any(char in endpoint for char in "\r\n\x00"):
        raise ValueError("endpoint must be non-empty, within 8,192 characters, and contain no control characters.")
    return validate_url_safety(endpoint)


def _json_object(raw: str, field_name: str) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field_name} must be valid JSON.") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object.")
    return value


def _safe_headers(raw: str) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    supplied = _json_object(raw, "headers")
    if len(supplied) > 100:
        raise ValueError("headers must contain at most 100 entries.")
    for key, value in supplied.items():
        name = str(key)
        text = str(value)
        if not name or any(char in name or char in text for char in "\r\n\x00"):
            raise ValueError("headers cannot contain empty names or control characters.")
        headers[name] = text
    token = os.getenv("GRAPHQL_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _safe_query(action: str, query: object) -> str:
    if action not in {"query", "mutation", "introspect"}:
        raise ValueError("action must be query, mutation, or introspect.")
    text = str(query or "").strip()
    if not text or len(text) > _MAX_QUERY_CHARS or "\x00" in text:
        raise ValueError("query must be non-empty, within 50,000 characters, and contain no null bytes.")
    lowered = text.lstrip().lower()
    if action == "mutation" and not lowered.startswith("mutation"):
        raise ValueError("mutation action requires a GraphQL mutation operation.")
    if action == "introspect" and "__schema" not in text and "__type" not in text:
        raise ValueError("introspect action requires a __schema or __type query.")
    if action != "mutation" and lowered.startswith("mutation"):
        raise ValueError("GraphQL mutations must use action='mutation' and require approval.")
    return text


def _read_response(response: httpx.Response) -> tuple[str, bool]:
    content = bytearray()
    truncated = False
    for chunk in response.iter_bytes():
        remaining = _MAX_RESPONSE_BYTES - len(content)
        if remaining <= 0:
            truncated = True
            break
        content.extend(chunk[:remaining])
        if len(chunk) > remaining:
            truncated = True
            break
    return content.decode(response.encoding or "utf-8", errors="replace"), truncated


def run(action: str, endpoint: str = "", query: str = "", variables: str = "", headers: str = "") -> str:
    """Execute a bounded GraphQL operation against a shared-policy-safe endpoint."""
    try:
        safe_endpoint = _safe_endpoint(endpoint)
        payload: dict[str, Any] = {"query": _safe_query(action, query)}
        parsed_variables = _json_object(variables, "variables")
        if variables:
            payload["variables"] = parsed_variables
        header_dict = _safe_headers(headers)

        with httpx.stream(
            "POST",
            safe_endpoint,
            json=payload,
            headers=header_dict,
            timeout=30,
            follow_redirects=False,
        ) as response:
            text, truncated = _read_response(response)
            if truncated:
                return "Error: GraphQL response exceeded the 256 KiB safety limit."
            if response.status_code != 200:
                return f"Error: {response.status_code} - {text[:200]}"

        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            return f"Error: GraphQL response was not valid JSON: {text[:200]}"
        if not isinstance(result, dict):
            return "Error: GraphQL response root must be a JSON object."
        if result.get("errors"):
            return "Errors: " + str(result["errors"])[:_MAX_OUTPUT_CHARS]
        return str(result.get("data", ""))[:_MAX_OUTPUT_CHARS]
    except (httpx.HTTPError, ValueError) as exc:
        return f"Error: {exc}"


# Email draft
def email_draft(action: str = "", to: str = "", subject: str = "", context: str = "") -> str:
    """Generate a professional email draft using the configured provider pool."""
    del action
    if not to or not context:
        return "Error: to and context required"

    try:
        from core.provider import ProviderPool

        pool = ProviderPool()
        prompt = f"""Generate a professional email draft:

To: {to}
Subject: {subject}
Context/Purpose: {context}

Write a clear, professional email:"""
        response = pool.chat_with_retry([{"role": "user", "content": prompt}])
        choices = response.get("choices", [])
        if not choices:
            return "Error: No response from AI provider"
        return (choices[0].get("message", {}).get("content", "") or "No content")[:4000]
    except Exception as exc:
        return f"Error: {exc}"


if __name__ == "__main__":
    print("GraphQL and Email plugins loaded.")
