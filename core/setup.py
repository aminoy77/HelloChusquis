import yaml
import httpx
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.table import Table

console = Console()
CONFIG_PATH = Path("config.yaml")

KNOWN_PROVIDERS = [
    {"name": "OpenRouter",      "base_url": "https://openrouter.ai/api/v1",          "docs": "openrouter.ai/keys"},
    {"name": "Ollama Cloud",    "base_url": "https://ollama.com/v1",                 "docs": "ollama.com → Sign in → API Keys"},
    {"name": "Anthropic Claude","base_url": "https://api.anthropic.com/v1",          "docs": "console.anthropic.com"},
    {"name": "OpenAI",          "base_url": "https://api.openai.com/v1",             "docs": "platform.openai.com/api-keys"},
    {"name": "Google Gemini",   "base_url": "https://generativelanguage.googleapis.com/v1beta/openai", "docs": "aistudio.google.com/apikey"},
    {"name": "Groq",            "base_url": "https://api.groq.com/openai/v1",        "docs": "console.groq.com/keys"},
    {"name": "xAI (Grok)",      "base_url": "https://api.x.ai/v1",                  "docs": "console.x.ai"},
    {"name": "Perplexity",      "base_url": "https://api.perplexity.ai",             "docs": "perplexity.ai/settings/api"},
    {"name": "Qwen / Alibaba",  "base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1", "docs": "dashscope.aliyuncs.com"},
    {"name": "MiniMax",         "base_url": "https://api.minimax.chat/v1",           "docs": "platform.minimax.io"},
    {"name": "Mistral",         "base_url": "https://api.mistral.ai/v1",             "docs": "console.mistral.ai/api-keys"},
    {"name": "DeepSeek",        "base_url": "https://api.deepseek.com/v1",           "docs": "platform.deepseek.com/api_keys"},
    {"name": "Cohere",          "base_url": "https://api.cohere.com/v1",             "docs": "dashboard.cohere.com/api-keys"},
    {"name": "Together AI",     "base_url": "https://api.together.xyz/v1",           "docs": "api.together.ai/settings/api-keys"},
    {"name": "Fireworks AI",    "base_url": "https://api.fireworks.ai/inference/v1", "docs": "fireworks.ai/account/api-keys"},
    {"name": "Blackbox AI",     "base_url": "https://api.blackbox.ai/v1",            "docs": "blackbox.ai"},
    {"name": "Xiaomi (MiMo)",   "base_url": "https://api.mimo.xiaomi.com/v1",        "docs": "mimo.xiaomi.com"},
    {"name": "Novita AI",       "base_url": "https://api.novita.ai/v3/openai",       "docs": "novita.ai/settings/key-management"},
    {"name": "Custom / Other",  "base_url": "",                                      "docs": ""},
]


def pick_provider() -> dict:
    table = Table(show_header=False, box=None, padding=(0, 2))
    for i, p in enumerate(KNOWN_PROVIDERS):
        table.add_row(f"[cyan]{i+1}[/cyan]", p["name"], f"[dim]{p['docs']}[/dim]")
    console.print(table)

    choice = IntPrompt.ask("  Pick a provider", default=1)
    idx = max(0, min(choice - 1, len(KNOWN_PROVIDERS) - 1))
    selected = KNOWN_PROVIDERS[idx]

    if selected["name"] == "Custom / Other":
        base_url = Prompt.ask("  Base URL")
    else:
        base_url = selected["base_url"]
        console.print(f"  [dim]Get your API key at: {selected['docs']}[/dim]")

    return {"name": selected["name"], "base_url": base_url}


def fetch_available_models(base_url: str, api_key: str) -> list[str]:
    try:
        with httpx.Client(timeout=10) as client:
            r = client.get(
                f"{base_url.rstrip('/')}/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            r.raise_for_status()
            data = r.json()
            models = [m["id"] for m in data.get("data", data.get("models", []))]
            return sorted(models)
    except Exception:
        return []


def pick_model(base_url: str, api_key: str) -> str:
    console.print("\n  [dim]Fetching available models...[/dim]")
    models = fetch_available_models(base_url, api_key)

    if models:
        table = Table(show_header=False, box=None, padding=(0, 2))
        for i, m in enumerate(models):
            table.add_row(f"[cyan]{i+1}[/cyan]", m)
        console.print(table)
        choice = IntPrompt.ask("  Pick a model", default=1)
        idx = max(0, min(choice - 1, len(models) - 1))
        return models[idx]
    else:
        console.print("  [yellow]Could not fetch models. Enter manually:[/yellow]")
        return Prompt.ask("  Model name", default="gpt-4o-mini")


def run_setup():
    console.print(Panel(
        "[bold cyan]HelloChusquis Setup[/bold cyan]\n[dim]Configure your AI providers[/dim]\n\n[yellow]⚠ Recommended: add at least 2 providers for fallback.[/yellow]",
        expand=False
    ))

    providers = []
    priority = 1

    while True:
        console.print(f"\n[bold]Provider #{priority}[/bold]")
        provider_info = pick_provider()
        api_key = Prompt.ask("  API Key", password=True)
        model = pick_model(provider_info["base_url"], api_key)

        providers.append({
            "name": f"{provider_info['name']}-{priority}",
            "base_url": provider_info["base_url"],
            "api_key": api_key,
            "model": model,
            "priority": priority,
        })

        console.print(f"  [green]✓[/green] Added: [cyan]{provider_info['name']}[/cyan] → [cyan]{model}[/cyan]")
        priority += 1

        if priority == 2:
            add_more = Confirm.ask("\n  Add another provider? [yellow](recommended)[/yellow]", default=True)
        else:
            add_more = Confirm.ask("\n  Add another provider?", default=False)

        if not add_more:
            if priority == 2:
                console.print("  [yellow]⚠ Only one provider configured. If it fails, HelloChusquis will stop working.[/yellow]")
            break

    reset_hours = IntPrompt.ask(
        "\nReset exhausted providers after how many hours?",
        default=1
    )

    retention_days = IntPrompt.ask(
        "Delete old sessions after how many days?",
        default=30
    )

    workspace = Prompt.ask(
        "Default workspace directory",
        default=str(Path.home() / "workspace")
    )

    # Auto-install plugins
    console.print("\n[bold]Plugin auto-install[/bold]")
    console.print("[dim]HelloChusquis can automatically install plugins when needed.[/dim]")
    auto_plugins = Confirm.ask(
        "Allow HelloChusquis to install plugins automatically? [yellow](recommended)[/yellow]",
        default=True
    )

    config = {
        "providers": providers,
        "settings": {
            "provider_reset_hours": reset_hours,
            "max_retries": 3,
            "timeout_seconds": 30,
            "workspace_dirs": [workspace],
            "memory_retention_days": retention_days,
            "auto_install_plugins": auto_plugins,
        },
        "agent": {
            "system_prompt": (
                "You are HelloChusquis, a powerful terminal AI assistant. "
                "You have access to tools: shell, files, code, and any installed plugins. "
                "Always be concise. When using tools, explain what you're doing. "
                "If the user asks for something you cannot do (like checking weather, "
                "controlling Spotify, etc.) but a plugin exists for it, tell them: "
                "'I can't do that natively, but you can install the [plugin_name] plugin "
                "with: hellochusquis install [plugin_name]'. "
                "If you don't know if a plugin exists, suggest they check: "
                "hellochusquis plugins"
            )
        }
    }

    CONFIG_PATH.write_text(yaml.dump(config, allow_unicode=True, sort_keys=False))
    console.print(f"\n[green]✓ Config saved to {CONFIG_PATH}[/green]")
    return config


def ensure_config() -> dict:
    if not CONFIG_PATH.exists():
        console.print("[yellow]No config found. Running setup...[/yellow]\n")
        return run_setup()
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)
