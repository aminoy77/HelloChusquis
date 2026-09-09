from __future__ import annotations

import time
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit
from pathlib import Path
from typing import List, Optional, Dict, Any

import httpx
import yaml

from core.logger import get_logger

logger = get_logger("provider")


def validate_provider_base_url(base_url: str) -> str:
    """Return a canonical provider endpoint or reject unsafe URL components."""
    if not isinstance(base_url, str):
        raise ValueError("Provider base URL must be a string")

    candidate = base_url.strip()
    try:
        parsed = urlsplit(candidate)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Provider base URL must have a valid host and port") from exc

    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Provider base URL must use http or https scheme")
    if not parsed.hostname:
        raise ValueError("Provider base URL must have a valid host")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("Provider base URL must not include credentials")
    if parsed.query or parsed.fragment:
        raise ValueError("Provider base URL must not include query or fragment")
    if port is not None and not 1 <= port <= 65535:
        raise ValueError("Provider base URL must have a valid host and port")

    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", ""))


def public_provider_base_url(base_url: str) -> str:
    """Return a redacted endpoint for status, including legacy configurations."""
    try:
        parsed = urlsplit(base_url)
        host = parsed.hostname
        port = parsed.port
    except (TypeError, ValueError):
        return "[invalid provider URL]"

    if parsed.scheme not in {"http", "https"} or not host:
        return "[invalid provider URL]"
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    netloc = f"{host}:{port}" if port is not None else host
    return urlunsplit((parsed.scheme, netloc, parsed.path.rstrip("/"), "", ""))


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

    def __init__(
        self,
        config_path: str | Path = "config.yaml",
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.providers: List[Provider] = []
        self.reset_after_seconds: float = 3600  # default 1 hour
        self.timeout: int = 15  # seconds
        self._models_cache: Dict[str, tuple] = {}  # name -> (fetched_at, models)
        if config is None:
            self._load(Path(config_path))
        else:
            self._load_config(config, source="provided configuration")

    # ---------------------------------------------------------------------
    # Configuration loading
    # ---------------------------------------------------------------------
    def _load(self, config_path: Path) -> None:
        """Load provider definitions from *config_path*.

        Configurations containing only local providers are valid: they have no
        API key by design, so the first existing file remains a candidate even
        when its valid-key count is zero.
        """
        from pathlib import Path as PathLib

        def load_config(path: Path) -> tuple[Optional[dict], int]:
            if not path.is_file():
                return None, 0
            with path.open() as f:
                loaded = yaml.safe_load(f) or {}
            providers_list = loaded.get("providers", [])
            if isinstance(providers_list, dict):
                providers_list = list(providers_list.values())
            valid_count = sum(
                1 for provider in providers_list if provider.get("api_key", "").strip()
            )
            return loaded, valid_count

        possible_paths = [
            config_path,
            PathLib.home() / "config.yaml",
            PathLib.home() / ".hellochusquis" / "config.yaml",
        ]
        best_config: Optional[dict] = None
        best_valid_count = -1
        best_path: Optional[Path] = None

        for path in possible_paths:
            loaded, valid_count = load_config(path)
            if loaded is not None and valid_count > best_valid_count:
                best_config = loaded
                best_valid_count = valid_count
                best_path = path
                if valid_count >= 2:
                    break

        if best_config is None or best_path is None:
            raise FileNotFoundError(
                f"Configuration file not found. Searched: {[str(path) for path in possible_paths]}"
            )
        self._load_config(best_config, source=str(best_path))

    def _load_config(self, config: Dict[str, Any], source: str) -> None:
        """Populate the pool from an already loaded configuration mapping."""
        settings = config.get("settings", {})
        self.reset_after_seconds = settings.get("provider_reset_hours", 1) * 3600
        self.timeout = settings.get("timeout_seconds", 15)

        providers_cfg_raw = config.get("providers", [])
        providers_list = (
            list(providers_cfg_raw.values())
            if isinstance(providers_cfg_raw, dict)
            else providers_cfg_raw
        )
        for provider_config in sorted(providers_list, key=lambda item: item.get("priority", 0)):
            provider = Provider(
                name=provider_config["name"],
                base_url=validate_provider_base_url(provider_config["base_url"]),
                api_key=provider_config.get("api_key", ""),
                model=provider_config["model"],
                priority=provider_config.get("priority", 0),
            )
            self.providers.append(provider)
        logger.info("Loaded %d providers from %s", len(self.providers), source)

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
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
    ) -> dict:
        """Attempt to chat, retrying up to *max_retries* times on failure.

        If *provider_name* is given, only that provider is tried. If *model*
        is given, it overrides the provider's configured model for this call.

        The method delegates to :meth:`chat` and catches :class:`RuntimeError`
        from failed providers.
        """
        last_error: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                return self.chat(messages, tools, provider_name=provider_name, model=model)
            except RuntimeError as exc:
                last_error = exc
                if attempt < max_retries - 1:
                    logger.warning(
                        "Chat attempt %d failed (%s); retrying", attempt + 1, exc
                    )
                    time.sleep(2)
                continue
        raise RuntimeError(f"All providers failed after {max_retries} attempts: {last_error}")

    def chat(self, messages: List[dict], tools: Optional[List[dict]] = None,
             provider_name: Optional[str] = None, model: Optional[str] = None) -> dict:
        """Send *messages* to the first available provider and return the response.

        When *provider_name* is supplied the pool only considers that provider;
        if it is unavailable the request still falls back to other providers so
        the UI selection is a preference, not a hard lock.

        Raises
        ------
        RuntimeError
            If no providers are ready or all attempts error.
        """
        available = self._available(tools)
        if not available:
            raise RuntimeError("All providers exhausted. Try again later.")

        if provider_name:
            preferred = [p for p in available if p.name == provider_name]
            if preferred:
                available = preferred

        last_error: Optional[Exception] = None
        for provider in available:
            start = time.time()
            try:
                result = self._call(provider, messages, tools, model=model)
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
        model: Optional[str] = None,
    ) -> dict:
        """Perform the HTTP request against *provider*.

        Returns the JSON payload on success; raises for HTTP errors.
        """
        payload: Dict[str, Any] = {
            "model": model or provider.model,
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
                    "base_url": public_provider_base_url(p.base_url),
                    "status": "exhausted" if p.exhausted else "ready",
                    "avg_ms": round(p.avg_response_time * 1000) if p.avg_response_time else 0,
                    "calls": p.total_calls,
                    "failures": p.failed_calls,
                }
            )
        return summary

    def list_models(self, name: str, refresh: bool = False) -> List[str]:
        """Return the models available for a provider, with a short TTL cache.

        Best-effort: if the provider's /models endpoint can't be reached the
        list falls back to the provider's configured model.
        """
        now = time.time()
        cached = self._models_cache.get(name)
        if not refresh and cached and (now - cached[0]) < 300:
            return cached[1]

        provider = next((p for p in self.providers if p.name == name), None)
        if provider is None:
            return []

        models: List[str] = []
        try:
            from core.setup import fetch_available_models
            models = fetch_available_models(provider.base_url, provider.api_key, provider_name=provider.name)
        except Exception:
            models = []

        if provider.model and provider.model not in models:
            models.insert(0, provider.model)

        self._models_cache[name] = (now, models)
        logger.info("Fetched %d models for %s", len(models), name)
        return models

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
                p.base_url = validate_provider_base_url(base_url)
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
        provider = Provider(
            name=name,
            api_key=api_key,
            base_url=validate_provider_base_url(base_url),
            model=model,
            priority=priority,
        )
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
