"""Loopback-only browser setup for local provider configuration."""
from __future__ import annotations

import copy
import json
import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from core.setup import (
    KNOWN_PROVIDERS,
    SYSTEM_PROMPT,
    _save_config_securely,
    ensure_config,
    fetch_available_models,
)

MAX_REQUEST_BYTES = 16_384


def _catalog() -> list[dict]:
    return [
        {
            "name": item["name"],
            "base_url": item["base_url"],
            "category": item.get("category", "Other"),
            "docs": item.get("docs", ""),
            "requires_key": item.get("requires_key", True),
            "models": list(item.get("models", [])),
        }
        for item in KNOWN_PROVIDERS
        if not item.get("oauth") and item.get("base_url")
    ]


def _find_existing_provider(config: dict, provider_info: dict) -> dict | None:
    providers = config.get("providers", [])
    if isinstance(providers, dict):
        providers = list(providers.values())
    if not isinstance(providers, list):
        return None
    return next(
        (
            provider
            for provider in providers
            if isinstance(provider, dict) and (
                str(provider.get("base_url") or "").rstrip("/") == provider_info["base_url"].rstrip("/")
            or provider.get("name") == provider_info["name"]
            )
        ),
        None,
    )


def setup_state(config: dict) -> dict:
    """Return display-safe setup state without revealing stored credentials."""
    catalog = _catalog()
    providers = config.get("providers", [])
    if isinstance(providers, dict):
        providers = list(providers.values())
    if not isinstance(providers, list):
        providers = []
    providers = [provider for provider in providers if isinstance(provider, dict)]
    selected = providers[0] if providers else {}
    matched = next(
        (
            item
            for item in catalog
            if item["base_url"].rstrip("/") == selected.get("base_url", "").rstrip("/")
            or item["name"] == selected.get("name")
        ),
        {},
    )
    existing = _find_existing_provider(config, matched) if matched else None
    configured = []
    for provider in providers:
        catalog_entry = next(
            (
                item for item in catalog
                if item["base_url"].rstrip("/") == str(provider.get("base_url") or "").rstrip("/")
                or item["name"] == provider.get("name")
            ),
            None,
        )
        if catalog_entry:
            configured.append(
                {
                    "name": catalog_entry["name"],
                    "base_url": catalog_entry["base_url"],
                    "model": provider.get("model", ""),
                    "key_configured": bool(provider.get("api_key")),
                }
            )
    return {
        "catalog": catalog,
        "provider": matched.get("name", ""),
        "model": selected.get("model", ""),
        "key_configured": bool((existing or {}).get("api_key")),
        "configured_providers": configured,
        "configured_count": len(providers),
    }


def save_provider_config(config: dict, payload: dict) -> dict:
    """Validate a browser submission, then persist it using the secure writer."""
    if not isinstance(payload, dict):
        raise ValueError("Choose a provider and model.")
    provider_name = payload.get("provider")
    provider_info = next((item for item in _catalog() if item["name"] == provider_name), None)
    if provider_info is None:
        raise ValueError("Choose a provider from the list.")

    model = payload.get("model")
    api_key = payload.get("api_key", "")
    if not isinstance(model, str) or not model.strip() or len(model) > 256:
        raise ValueError("Enter a model name (up to 256 characters).")
    if not isinstance(api_key, str) or len(api_key) > 8_192:
        raise ValueError("The API key is too long.")

    updated = copy.deepcopy(config)
    providers = updated.setdefault("providers", [])
    if isinstance(providers, dict):
        providers = list(providers.values())
        updated["providers"] = providers
    elif not isinstance(providers, list):
        providers = updated["providers"] = []
    current = _find_existing_provider(updated, provider_info)
    key = api_key.strip() or (current or {}).get("api_key", "")

    if provider_info["requires_key"] and not key:
        raise ValueError("Add an API key for this provider, or choose a local provider.")

    if not provider_info["requires_key"]:
        key = "ollama" if "ollama" in provider_info["name"].lower() else ""

    if current:
        current["base_url"] = provider_info["base_url"]
        current["model"] = model.strip()
        current["api_key"] = key
    else:
        providers.append(
            {
                "name": provider_info["name"],
                "base_url": provider_info["base_url"],
                "api_key": key,
                "model": model.strip(),
                "priority": max((p.get("priority", 0) for p in providers), default=0) + 1,
            }
        )

    settings = updated.get("settings")
    if not isinstance(settings, dict):
        settings = updated["settings"] = {}
    settings.setdefault("provider_reset_hours", 1)
    settings.setdefault("max_retries", 3)
    settings.setdefault("timeout_seconds", 15)
    settings.setdefault("memory_retention_days", 30)
    settings.setdefault("thinking", "auto")
    default_workspace = str(Path.home() / ".hellochusquis" / "workspace")
    workspace_dirs = settings.get("workspace_dirs")
    if not isinstance(workspace_dirs, list) or not workspace_dirs:
        settings["workspace_dirs"] = [default_workspace]
    Path(str(settings["workspace_dirs"][0])).expanduser().mkdir(parents=True, exist_ok=True)
    agent = updated.setdefault("agent", {})
    if not isinstance(agent, dict):
        agent = updated["agent"] = {}
    if not isinstance(agent.get("system_prompt"), str) or len(agent.get("system_prompt", "")) < 100:
        agent["system_prompt"] = SYSTEM_PROMPT

    _save_config_securely(updated)
    return updated


class _SetupServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class _SetupHandler(BaseHTTPRequestHandler):
    server: _SetupServer

    def log_message(self, _format: str, *args) -> None:
        # Setup URLs contain a short-lived access token; never log request paths.
        return

    def _local_request(self) -> bool:
        expected = f"127.0.0.1:{self.server.server_port}"
        return self.headers.get("Host", "").lower() == expected

    def _authorized(self, require_origin: bool = False) -> bool:
        origin = self.headers.get("Origin")
        expected_origin = f"http://127.0.0.1:{self.server.server_port}"
        return (
            self._local_request()
            and self.headers.get("X-Setup-Token") == self.server.setup_token
            and (origin == expected_origin if require_origin else origin in (None, expected_origin))
        )

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, data: dict) -> None:
        self._send(status, json.dumps(data).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self) -> None:
        if not self._local_request():
            self._send_json(403, {"error": "Local setup access only."})
            return

        request = urlsplit(self.path)
        if request.path == "/":
            token = parse_qs(request.query).get("token", [""])[0]
            if not secrets.compare_digest(token, self.server.setup_token):
                self._send(403, b"Setup link expired. Run the setup command again.", "text/plain; charset=utf-8")
                return
            nonce = secrets.token_urlsafe(18)
            html = (Path(__file__).with_name("setup.html").read_text(encoding="utf-8")
                    .replace("__SETUP_NONCE__", nonce)
                    .replace("__SETUP_TOKEN__", self.server.setup_token))
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                f"default-src 'self'; script-src 'nonce-{nonce}'; style-src 'self' 'unsafe-inline'; "
                "connect-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'; object-src 'none'",
            )
            body = html.encode("utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if request.path == "/logo.png":
            token = parse_qs(request.query).get("token", [""])[0]
            if not secrets.compare_digest(token, self.server.setup_token):
                self._send(403, b"Setup link expired.", "text/plain; charset=utf-8")
                return
            image = Path(__file__).with_name("logo.png").read_bytes()
            self._send(200, image, "image/png")
            return

        if not self._authorized():
            self._send_json(403, {"error": "Setup link expired. Run the setup command again."})
            return
        if request.path == "/api/state":
            self._send_json(200, setup_state(self.server.config))
            return
        self._send_json(404, {"error": "Not found."})

    def do_POST(self) -> None:
        if not self._authorized(require_origin=True):
            self._send_json(403, {"error": "Setup access denied. Reopen the local setup page."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"error": "Invalid request size."})
            return
        if not 0 < length <= MAX_REQUEST_BYTES:
            self._send_json(413, {"error": "Request is empty or too large."})
            return
        if self.headers.get_content_type() != "application/json":
            self._send_json(415, {"error": "Expected a JSON request."})
            return
        try:
            payload = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, {"error": "Could not read the setup form."})
            return
        if not isinstance(payload, dict):
            self._send_json(400, {"error": "Could not read the setup form."})
            return

        request = urlsplit(self.path)
        if request.path == "/api/models":
            provider_info = next(
                (item for item in _catalog() if item["name"] == payload.get("provider")),
                None,
            )
            if provider_info is None:
                self._send_json(400, {"error": "Choose a provider from the list."})
                return
            key = payload.get("api_key", "")
            if not isinstance(key, str) or len(key) > 8_192:
                self._send_json(400, {"error": "The API key is too long."})
                return
            existing = _find_existing_provider(self.server.config, provider_info)
            models = fetch_available_models(
                provider_info["base_url"],
                key.strip() or (existing or {}).get("api_key", ""),
                provider_name=provider_info["name"],
            )
            self._send_json(200, {"models": models})
            return

        if request.path == "/api/save":
            try:
                self.server.config = save_provider_config(self.server.config, payload)
            except ValueError as exc:
                self._send_json(400, {"error": str(exc)})
                return
            except OSError:
                self._send_json(500, {"error": "Could not save configuration. Check local disk access."})
                return
            self._send_json(200, {"ok": True})
            self.server.saved.set()
            return

        self._send_json(404, {"error": "Not found."})


def run_setup_frontend(on_url=None) -> dict:
    """Open the local setup page and wait until the user saves a provider."""
    try:
        config = ensure_config(interactive=False)
    except FileNotFoundError:
        config = {}

    server = _SetupServer(("127.0.0.1", 0), _SetupHandler)
    server.setup_token = secrets.token_urlsafe(24)
    server.config = config
    server.saved = threading.Event()
    server.timeout = 0.25
    url = f"http://127.0.0.1:{server.server_port}/?token={server.setup_token}"
    try:
        if on_url:
            on_url(url)
        else:
            print(f"Configure HelloChusquis in your browser: {url}")
        try:
            if not webbrowser.open(url) and not on_url:
                print("If the browser did not open, copy the local URL above. Press Ctrl+C to cancel.")
        except Exception:
            if not on_url:
                print("Open the local URL above in your browser. Press Ctrl+C to cancel.")

        while not server.saved.is_set():
            server.handle_request()
    finally:
        server.server_close()
    return ensure_config(interactive=False)
