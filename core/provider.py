import httpx
import yaml
import time
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path
from rich.console import Console



console = Console()


@dataclass
class Provider:
    name: str
    base_url: str
    api_key: str
    model: str
    priority: int
    exhausted: bool = False
    exhausted_at: float = 0.0


class ProviderPool:
    def __init__(self, config_path: str = "config.yaml"):
        self.providers: list[Provider] = []
        self.reset_after_seconds: float = 3600
        self.timeout = 30
        self._load(config_path)

    def _load(self, config_path: str):
        with open(config_path) as f:
            config = yaml.safe_load(f)

        self.reset_after_seconds = (
            config.get("settings", {}).get("provider_reset_hours", 1) * 3600
        )
        self.timeout = config.get("settings", {}).get("timeout_seconds", 30)

        for p in sorted(config["providers"], key=lambda x: x["priority"]):
            self.providers.append(Provider(
                name=p["name"],
                base_url=p["base_url"].rstrip("/"),
                api_key=p["api_key"],
                model=p["model"],
                priority=p["priority"],
            ))

    def _reset_if_needed(self, provider: Provider):
        if provider.exhausted:
            elapsed = time.time() - provider.exhausted_at
            if elapsed >= self.reset_after_seconds:
                provider.exhausted = False
                provider.exhausted_at = 0.0

    def _available(self) -> list[Provider]:
        for p in self.providers:
            self._reset_if_needed(p)
        return [p for p in self.providers if not p.exhausted]

    def chat_with_retry(self, messages: list[dict], tools=None, max_retries: int = 3) -> dict:
        for attempt in range(max_retries):
            try:
                return self.chat(messages, tools)
            except RuntimeError:
                if attempt < max_retries - 1:
                    console.print(f"[dim]Retrying... ({attempt + 2}/{max_retries})[/dim]")
                    time.sleep(2)
        raise RuntimeError("All providers failed after retries.")

    def chat(self, messages: list[dict], tools: Optional[list] = None) -> dict:
        available = self._available()
        if not available:
            raise RuntimeError("All providers exhausted. Try again later.")

        # Si hay tools, prioriza providers que los soporten
        if tools:
            tools_available = [p for p in available if "groq.com" not in p.base_url.lower()]
            if tools_available:
                available = tools_available

        last_error = None
        for provider in available:
            try:
                result = self._call(provider, messages, tools)
                return result
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                try:
                    error_body = e.response.json()
                    error_msg = error_body.get("error", {}).get("message", "Unknown error")
                except Exception:
                    error_msg = "Unknown error"

                if status == 429:
                    console.print(f"[yellow]↻ {provider.name} rate limited, switching...[/yellow]")
                    provider.exhausted = True
                    provider.exhausted_at = time.time()
                elif status in (402, 403):
                    console.print(f"[yellow]↻ {provider.name} quota exceeded, switching...[/yellow]")
                    provider.exhausted = True
                    provider.exhausted_at = time.time()
                elif status == 404:
                    console.print(f"[yellow]↻ {provider.name} model not found, switching...[/yellow]")
                elif status == 400:
                    console.print(f"[yellow]↻ {provider.name} bad request, switching...[/yellow]")
                elif status == 401:
                    console.print(f"[red]✗ {provider.name} invalid API key.[/red]")
                else:
                    console.print(f"[yellow]↻ {provider.name} error {status}, switching...[/yellow]")
                last_error = e
                continue
            except httpx.TimeoutException:
                console.print(f"[yellow]↻ {provider.name} timeout, switching...[/yellow]")
                last_error = Exception(f"{provider.name} timed out")
                continue
            except httpx.ConnectError:
                console.print(f"[yellow]↻ {provider.name} connection failed, switching...[/yellow]")
                last_error = Exception(f"{provider.name} connection failed")
                continue

        raise RuntimeError(f"All providers failed. Last error: {last_error}")

    def _call(self, provider: Provider, messages: list[dict], tools: Optional[list]) -> dict:
        payload = {
            "model": provider.model,
            "messages": messages,
        }

        provider_supports_tools = "groq.com" not in provider.base_url.lower()

        if tools and provider_supports_tools:
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

    def status(self) -> list[dict]:
        result = []
        for p in self.providers:
            self._reset_if_needed(p)
            result.append({
                "name": p.name,
                "model": p.model,
                "status": "exhausted" if p.exhausted else "ready",
            })
        return result
