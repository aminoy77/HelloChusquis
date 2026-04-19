import httpx
import yaml
import time
from dataclasses import dataclass, field
from typing import Optional
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
    avg_response_time: float = 0.0
    total_calls: int = 0
    failed_calls: int = 0


class ProviderPool:
    def __init__(self, config_path: str = "config.yaml"):
        self.providers: list[Provider] = []
        self.reset_after_seconds: float = 3600
        self.timeout = 15  # 15s — si falla en 15s, falla. No esperamos 30s.
        self._load(config_path)

    def _load(self, config_path: str):
        with open(config_path) as f:
            config = yaml.safe_load(f)

        self.reset_after_seconds = (
            config.get("settings", {}).get("provider_reset_hours", 1) * 3600
        )
        self.timeout = config.get("settings", {}).get("timeout_seconds", 15)

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

    def _available(self, tools: Optional[list] = None) -> list[Provider]:
        for p in self.providers:
            self._reset_if_needed(p)
        available = [p for p in self.providers if not p.exhausted]

        if tools:
            tools_capable = [p for p in available if "groq.com" not in p.base_url.lower()]
            if tools_capable:
                return tools_capable

        return available

    def chat_with_retry(self, messages: list[dict], tools=None, max_retries: int = 2) -> dict:
        # max_retries reducido a 2 — 3 era demasiado y sumaba 4s de sleep
        last_error = None
        for attempt in range(max_retries):
            try:
                return self.chat(messages, tools)
            except RuntimeError as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Sin sleep — los providers ya se marcan exhausted
                    # No hay razón para esperar si ya cambiamos de provider
                    pass
        raise RuntimeError(f"All providers failed: {last_error}")

    def chat(self, messages: list[dict], tools: Optional[list] = None) -> dict:
        available = self._available(tools)
        if not available:
            raise RuntimeError("All providers exhausted. Try again later.")

        last_error = None
        for provider in available:
            start = time.time()
            try:
                result = self._call(provider, messages, tools)
                # Track response time
                elapsed = time.time() - start
                provider.avg_response_time = (
                    (provider.avg_response_time * provider.total_calls + elapsed)
                    / (provider.total_calls + 1)
                )
                provider.total_calls += 1
                return result

            except httpx.HTTPStatusError as e:
                provider.failed_calls += 1
                status = e.response.status_code
                try:
                    error_msg = e.response.json().get("error", {}).get("message", "")
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
                elif status == 400:
                    console.print(f"[yellow]↻ {provider.name} bad request[/yellow]")
                else:
                    console.print(f"[yellow]↻ {provider.name} error {status}[/yellow]")

                last_error = e
                continue

            except httpx.TimeoutException:
                provider.failed_calls += 1
                console.print(f"[yellow]↻ {provider.name} timeout[/yellow]")
                last_error = Exception(f"{provider.name} timed out")
                continue

            except httpx.ConnectError:
                provider.failed_calls += 1
                console.print(f"[yellow]↻ {provider.name} connection failed[/yellow]")
                last_error = Exception(f"{provider.name} connection failed")
                continue

        raise RuntimeError(f"All providers failed. Last: {last_error}")

    def _call(self, provider: Provider, messages: list[dict], tools: Optional[list]) -> dict:
        payload = {
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

    def status(self) -> list[dict]:
        result = []
        for p in self.providers:
            self._reset_if_needed(p)
            result.append({
                "name": p.name,
                "model": p.model,
                "status": "exhausted" if p.exhausted else "ready",
                "avg_ms": round(p.avg_response_time * 1000) if p.avg_response_time else 0,
                "calls": p.total_calls,
                "failures": p.failed_calls,
            })
        return result