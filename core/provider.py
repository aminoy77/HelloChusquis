from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any

import httpx
import yaml
from rich.console import Console

# Configure a basic logger – developers can adjust the level as needed.
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

console = Console()


@dataclass
class Provider:
    """Configuration and runtime state for a single LLM provider."""

    name: str
    base_url: str
    api_key: str
    model: str
    priority: int
    exhausted: bool = False
    exhausted_at: float = 0.0
    avg_response_time: float = 0.0
    total_calls: int = 0
    failed_calls: int = 0


class ProviderPool:
    """Manage a collection of :class:`Provider` instances.

    The pool loads providers from a YAML configuration file, selects an
    available provider for each request, and tracks simple performance
    metrics.
    """

    def __init__(self, config_path: str | Path = "config.yaml") -> None:
        self.providers: List[Provider] = []
        self.reset_after_seconds: float = 3600  # default 1 hour
        self.timeout: int = 15  # seconds
        self._load(Path(config_path))

    # ---------------------------------------------------------------------
    # Configuration loading
    # ---------------------------------------------------------------------
    def _load(self, config_path: Path) -> None:
        """Load provider definitions from *config_path*.

        Raises
        ------
        FileNotFoundError
            If the configuration file does not exist.
        yaml.YAMLError
            If the YAML cannot be parsed.
        """
        if not config_path.is_file():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with config_path.open() as f:
            config: Dict[str, Any] = yaml.safe_load(f) or {}

        settings = config.get("settings", {})
        self.reset_after_seconds = settings.get("provider_reset_hours", 1) * 3600
        self.timeout = settings.get("timeout_seconds", 15)

        providers_cfg = config.get("providers", [])
        for p in sorted(providers_cfg, key=lambda x: x.get("priority", 0)):
            provider = Provider(
                name=p["name"],
                base_url=p["base_url"].rstrip("/"),
                api_key=p["api_key"],
                model=p["model"],
                priority=p["priority"],
            )
            self.providers.append(provider)
        logger.info("Loaded %d providers from %s", len(self.providers), config_path)

    # ---------------------------------------------------------------------
    # Provider state helpers
    # ---------------------------------------------------------------------
    def _reset_if_needed(self, provider: Provider) -> None:
        """Reset *provider* if its exhausted interval has passed."""
        if provider.exhausted:
            elapsed = time.time() - provider.exhausted_at
            if elapsed >= self.reset_after_seconds:
                provider.exhausted = False
                provider.exhausted_at = 0.0
                logger.debug("Provider %s reset after %s seconds", provider.name, elapsed)

    def _available(self, tools: Optional[List[dict]] = None) -> List[Provider]:
        """Return a list of providers that are not currently exhausted.

        If *tools* is supplied, providers that cannot handle tools (e.g., Groq)
        are filtered out.
        """
        for p in self.providers:
            self._reset_if_needed(p)
        available = [p for p in self.providers if not p.exhausted]

        if tools:
            # Example rule: providers whose base_url contains "groq.com" do not
            # support tool usage.
            capable = [p for p in available if "groq.com" not in p.base_url.lower()]
            return capable or available
        return available

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def chat_with_retry(
        self,
        messages: List[dict],
        tools: Optional[List[dict]] = None,
        max_retries: int = 3,
    ) -> dict:
        """Attempt to chat, retrying up to *max_retries* times on failure.

        The method delegates to :meth:`chat` and catches :class:`RuntimeError`
        from failed providers.
        """
        last_error: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                return self.chat(messages, tools)
            except RuntimeError as exc:
                last_error = exc
                if attempt < max_retries - 1:
                    logger.warning(
                        "Chat attempt %d failed (%s); retrying", attempt + 1, exc
                    )
                    time.sleep(2)
                continue
        raise RuntimeError(f"All providers failed after {max_retries} attempts: {last_error}")

    def chat(self, messages: List[dict], tools: Optional[List[dict]] = None) -> dict:
        """Send *messages* to the first available provider and return the response.

        Raises
        ------
        RuntimeError
            If no providers are ready or all attempts error.
        """
        available = self._available(tools)
        if not available:
            raise RuntimeError("All providers exhausted. Try again later.")

        last_error: Optional[Exception] = None
        for provider in available:
            start = time.time()
            try:
                result = self._call(provider, messages, tools)
                # Update timing statistics
                elapsed = time.time() - start
                provider.avg_response_time = (
                    (provider.avg_response_time * provider.total_calls + elapsed)
                    / (provider.total_calls + 1)
                )
                provider.total_calls += 1
                return result
            except httpx.HTTPStatusError as e:
                provider.failed_calls += 1
                self._handle_http_error(provider, e)
                last_error = e
                continue
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                provider.failed_calls += 1
                console.print(f"[yellow]↻ {provider.name} {e.__class__.__name__}[/yellow]")
                logger.debug("%s error for provider %s: %s", e.__class__.__name__, provider.name, e)
                last_error = e
                continue
        raise RuntimeError(f"All providers failed. Last error: {last_error}")

    # ---------------------------------------------------------------------
    # Helper methods for error handling and API calls
    # ---------------------------------------------------------------------
    def _handle_http_error(self, provider: Provider, error: httpx.HTTPStatusError) -> None:
        """Log and mark the provider based on HTTP status codes.

        The provider is marked *exhausted* for rate-limit, quota, or auth errors.
        """
        status = error.response.status_code
        try:
            error_msg = error.response.json().get("error", {}).get("message", "")
        except Exception:
            error_msg = ""

        if status == 429:
            console.print(f"[yellow]↻ {provider.name} rate limited[/yellow]")
            provider.exhausted = True
            provider.exhausted_at = time.time()
        elif status in (402, 403):
            console.print(f"[yellow]↻ {provider.name} quota exceeded[/yellow]")
            provider.exhausted = True
            provider.exhausted_at = time.time()
        elif status == 401:
            console.print(f"[red]✗ {provider.name} invalid API key[/red]")
            provider.exhausted = True
            provider.exhausted_at = time.time()
        elif status == 404:
            console.print(f"[yellow]↻ {provider.name} model not found[/yellow]")
            # No exhausted — el provider funciona, solo el modelo no existe
        elif status == 400:
            console.print(f"[yellow]↻ {provider.name} bad request[/yellow]")
            # No exhausted — puede ser un problema del payload, no del provider
        else:
            console.print(f"[yellow]↻ {provider.name} error {status}[/yellow]")
            provider.exhausted = True
            provider.exhausted_at = time.time()

        logger.info(
            "Provider %s handled HTTP error (status %s). Message: %s",
            provider.name,
            status,
            error_msg,
        )

    def _call(
        self,
        provider: Provider,
        messages: List[dict],
        tools: Optional[List[dict]],
    ) -> dict:
        """Perform the HTTP request against *provider*.

        Returns the JSON payload on success; raises for HTTP errors.
        """
        payload: Dict[str, Any] = {
            "model": provider.model,
            "messages": messages,
        }
        supports_tools = "groq.com" not in provider.base_url.lower()
        if tools and supports_tools:
            payload["tools"] = tools

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{provider.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {provider.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    def status(self) -> List[dict]:
        """Return a summary of each provider's current state.

        The dict contains the name, model, readiness, average latency (ms),
        total calls and failures.
        """
        summary: List[dict] = []
        for p in self.providers:
            self._reset_if_needed(p)
            summary.append(
                {
                    "name": p.name,
                    "model": p.model,
                    "status": "exhausted" if p.exhausted else "ready",
                    "avg_ms": round(p.avg_response_time * 1000) if p.avg_response_time else 0,
                    "calls": p.total_calls,
                    "failures": p.failed_calls,
                }
            )
        return summary
