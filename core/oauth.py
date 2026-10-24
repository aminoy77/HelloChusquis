"""OAuth device-flow login helpers for LLM providers (RFC 8628).

Tokens are stored by the caller in the provider config; this module only
acquires and refreshes them. Full token values are never printed.
"""
from __future__ import annotations

import time
import webbrowser
from typing import Callable, Optional

import httpx
from rich.console import Console

console = Console()
_console = console


class OAuthError(Exception):
    """User-facing OAuth failure; str(self) is safe to print."""


def print_user_code(user_code: str, verification_uri: str,
                    console: Optional[Console] = None) -> None:
    """Show the verification URI + user code. Never prints tokens."""
    out = console or _console
    out.print(f"\n[bold cyan]Open this URL in your browser:[/bold cyan] {verification_uri}")
    out.print(f"[bold]Enter code:[/bold] [bold yellow]{user_code}[/bold yellow]\n")


def device_flow(device_url: str, token_url: str, client_id: str, scope: str,
                open_browser: Callable[[str], None] = webbrowser.open,
                poll_interval: int = 5, timeout: float = 300.0,
                console_: Optional[Console] = None) -> dict:
    """Run an RFC 8628 device-code flow and return the token endpoint JSON.

    Raises OAuthError on timeout, denial, or expiry.
    """
    resp = httpx.post(device_url, data={"client_id": client_id, "scope": scope},
                      timeout=15)
    resp.raise_for_status()
    dev = resp.json()
    user_code = dev.get("user_code", "")
    verification_uri = dev.get("verification_uri", "")
    interval = int(dev.get("interval", poll_interval))
    expires_in = float(dev.get("expires_in", timeout))

    print_user_code(user_code, verification_uri, console_)
    open_browser(verification_uri)

    deadline = time.time() + min(expires_in, timeout)
    interval = max(interval, 1)
    while time.time() < deadline:
        time.sleep(interval)
        tok = httpx.post(token_url, data={
            "client_id": client_id,
            "device_code": dev["device_code"],
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        }, timeout=15)
        tok.raise_for_status()
        payload = tok.json()
        if "access_token" in payload:
            return payload
        error = payload.get("error")
        if error == "authorization_pending":
            continue
        if error == "slow_down":
            interval += 5
            continue
        if error == "expired_token":
            raise OAuthError("Device code expired — try logging in again.")
        if error == "access_denied":
            raise OAuthError("Authorization denied in the browser.")
        if error:
            raise OAuthError(f"OAuth error: {error}")
    raise OAuthError("Timed out waiting for authorization — try again.")
