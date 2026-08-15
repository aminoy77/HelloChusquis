from __future__ import annotations

import os
import httpx

PLUGIN_NAME = "sendgrid"
PLUGIN_DESCRIPTION = "SendGrid transactional email and marketing"


def run(action: str, **kwargs) -> str:
    api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@example.com")
    if not api_key:
        return "Error: No SendGrid API key found. Set SENDGRID_API_KEY environment variable."

    base_url = "https://api.sendgrid.com/v3"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        if action == "send_email":
            to = kwargs.get("to")
            subject = kwargs.get("subject")
            content = kwargs.get("content")
            html = kwargs.get("html", content)
            if not to or not subject or not content:
                return "Error: to, subject, and content are required for send_email"
            payload = {
                "personalizations": [{"to": [{"email": to}]}],
                "from": {"email": from_email},
                "subject": subject,
                "content": [
                    {"type": "text/plain", "value": content},
                    {"type": "text/html", "value": html},
                ],
            }
            r = httpx.post(f"{base_url}/mail/send", headers=headers, json=payload, timeout=30)
            if r.status_code in (200, 201, 202):
                return f"Email sent to {to} (status {r.status_code})"
            return f"Error: SendGrid returned {r.status_code}: {r.text[:300]}"

        elif action == "list_contacts":
            r = httpx.get(f"{base_url}/marketing/contacts", headers=headers, timeout=30)
            return _fmt(r)

        elif action == "get_stats":
            r = httpx.get(f"{base_url}/stats/global", headers=headers, timeout=30)
            return _fmt(r)

        else:
            return f"Error: Unknown action '{action}'. Available: send_email, list_contacts, get_stats"
    except httpx.TimeoutException:
        return "Error: Request timed out after 30 seconds."
    except Exception as e:
        return f"Error: {e}"


def _fmt(r: httpx.Response) -> str:
    try:
        return str(r.json())
    except Exception:
        return r.text[:500]