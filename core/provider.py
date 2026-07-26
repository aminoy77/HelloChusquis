from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any

import httpx
import yaml

from core.logger import get_logger

logger = get_logger("provider")


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
        from pathlib import Path as PathLib

        def load_config(path):
            """Load config from path, return (config_dict, provider_count) or (None, 0)."""
            if not path.is_file():
                return None, 0
            with path.open() as f:
                config = yaml.safe_load(f) or {}
            providers_list = config.get("providers", [])
            if isinstance(providers_list, dict):
                providers_list = list(providers_list.values())
            # Count providers with valid API keys
            valid_count = sum(1 for p in providers_list if p.get("api_key", "").strip())
            return config, valid_count

        # Check multiple locations for config, preferring ones with valid API keys
        possible_paths = [
            PathLib.home() / "config.yaml",
            PathLib.home() / ".hellochusquis" / "config.yaml",
            config_path,  # Current directory last (often has empty placeholder)
        ]

        best_config = None
        best_valid_count = 0
        best_path = None

        for path in possible_paths:
            config, valid_count = load_config(path)
            if config is not None and valid_count > best_valid_count:
                best_config = config
                best_valid_count = valid_count
                best_path = path
                if valid_count >= 2:  # Found a config with at least 2 valid providers
                    break

        if best_config is None:
            raise FileNotFoundError(f"Configuration file not found. Searched: {[str(p) for p in possible_paths]}")

        config = best_config

        settings = config.get("settings", {})
        self.reset_after_seconds = settings.get("provider_reset_hours", 1) * 3600
        self.timeout = settings.get("timeout_seconds", 15)

        providers_cfg_raw = config.get("providers", [])
        providers_list = list(providers_cfg_raw.values()) if isinstance(providers_cfg_raw, dict) else providers_cfg_raw
        
        for p in sorted(providers_list, key=lambda x: x.get("priority", 0)):
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
        Silently skips without showing errors to the user.
        """
        status = error.response.status_code
        try:
            error_msg = error.response.json().get("error", {}).get("message", "")
        except Exception:
            error_msg = ""

        if status in (429, 402, 403, 401, 400, 500, 502, 503, 504):
            # Mark as exhausted silently - no user-visible output
            provider.exhausted = True
            provider.exhausted_at = time.time()
        elif status == 404:
            # No exhausted — the provider works, just the model doesn't exist
            pass
        else:
            # Mark other errors as exhausted silently
            provider.exhausted = True
            provider.exhausted_at = time.time()

        logger.debug(
            "Provider %s HTTP error (status %s). Message: %s",
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
        if not provider.base_url.startswith(('http://', 'https://')):
            provider.base_url = 'https://' + provider.base_url

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

    def update_api_key(self, name: str, api_key: str):
        """Update API key for a provider."""
        for p in self.providers:
            if p.name == name:
                p.api_key = api_key
                logger.info("Updated API key for %s", name)
                return True
        return False

    def update_base_url(self, name: str, base_url: str):
        """Update base URL for a provider."""
        for p in self.providers:
            if p.name == name:
                p.base_url = base_url
                logger.info("Updated base URL for %s", name)
                return True
        return False

    def update_model(self, name: str, model: str):
        """Update model for a provider."""
        for p in self.providers:
            if p.name == name:
                p.model = model
                logger.info("Updated model for %s to %s", name, model)
                return True
        return False

    def add_provider(self, name: str, api_key: str, base_url: str, model: str, priority: int = 1):
        """Add a new provider."""
        provider = Provider(name=name, api_key=api_key, base_url=base_url, model=model, priority=priority)
        self.providers.append(provider)
        logger.info("Added provider %s", name)
        return True

    def remove_provider(self, name: str):
        """Remove a provider."""
        original = len(self.providers)
        self.providers = [p for p in self.providers if p.name != name]
        if len(self.providers) < original:
            logger.info("Removed provider %s", name)
            return True
        return False
