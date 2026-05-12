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
    # Major Providers
    {"name": "Groq",            "base_url": "https://api.groq.com/openai/v1",                          "docs": "console.groq.com/keys"},
    {"name": "OpenRouter",      "base_url": "https://openrouter.ai/api/v1",                            "docs": "openrouter.ai/keys"},
    {"name": "Ollama (local)",  "base_url": "http://localhost:11434/v1",                               "docs": "ollama.ai — runs locally, no API key needed"},
    {"name": "Anthropic Claude","base_url": "https://api.anthropic.com/v1",                            "docs": "console.anthropic.com"},
    {"name": "OpenAI",          "base_url": "https://api.openai.com/v1",                               "docs": "platform.openai.com/api-keys"},
    {"name": "Google Gemini",   "base_url": "https://generativelanguage.googleapis.com/v1beta/openai", "docs": "aistudio.google.com/apikey"},
    {"name": "xAI (Grok)",      "base_url": "https://api.x.ai/v1",                                    "docs": "console.x.ai"},
    {"name": "Perplexity",      "base_url": "https://api.perplexity.ai",                               "docs": "perplexity.ai/settings/api"},
    
    # Chinese Providers
    {"name": "Qwen / Alibaba",  "base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1", "docs": "dashscope.aliyuncs.com"},
    {"name": "MiniMax",         "base_url": "https://api.minimax.chat/v1",                             "docs": "platform.minimax.io"},
    {"name": "Baichuan",       "base_url": "https://api.baichuan-ai.com/v1",                        "docs": "platform.baichuan-ai.com"},
    {"name": "Zhipu (ChatGLM)", "base_url": "https://open.bigmodel.cn/api/paas/v4",                "docs": "open.bigmodel.cn"},
    {"name": "Moonshot",        "base_url": "https://api.moonshot.cn/v1",                             "docs": "platform.moonshot.cn"},
    
    # European Providers
    {"name": "Mistral",         "base_url": "https://api.mistral.ai/v1",                               "docs": "console.mistral.ai/api-keys"},
    {"name": "DeepSeek",        "base_url": "https://api.deepseek.com/v1",                             "docs": "platform.deepseek.com/api_keys"},
    {"name": "Cohere",          "base_url": "https://api.cohere.com/v1",                               "docs": "dashboard.cohere.com/api-keys"},
    
    # AI Platforms
    {"name": "Together AI",     "base_url": "https://api.together.xyz/v1",                             "docs": "api.together.ai/settings/api-keys"},
    {"name": "Fireworks AI",    "base_url": "https://api.fireworks.ai/inference/v1",                   "docs": "fireworks.ai/account/api-keys"},
    {"name": "Novita AI",       "base_url": "https://api.novita.ai/v3/openai",                         "docs": "novita.ai/settings/key-management"},
    {"name": "Lepton AI",       "base_url": "https://api.lepton.ai/httpapi/v1",                        "docs": "dashboard.lepton.ai"},
    {"name": "Hyperbolic",      "base_url": "https://api.hyperbolic.xyz/v1",                           "docs": "hyperbolic.xyz/dashboard"},
    {"name": "SambaNova",       "base_url": "https://api.sambanova.ai/v1",                             "docs": "cloud.sambanova.ai"},
    
    # Open Source Focused
    {"name": "Blackbox AI",     "base_url": "https://api.blackbox.ai/v1",                              "docs": "blackbox.ai"},
    {"name": "Xiaomi (MiMo)",   "base_url": "https://api.mimo.xiaomi.com/v1",                         "docs": "mimo.xiaomi.com"},
    {"name": "Replicate",       "base_url": "https://api.replicate.com/v1",                            "docs": "replicate.com/account/tokens"},
    {"name": "HuggingFace",     "base_url": "https://api-inference.huggingface.co/v1",               "docs": "huggingface.co/settings/tokens"},
    {"name": "Anyscale",        "base_url": "https://api.endpoints.anyscale.com/v1",                    "docs": "anyscale.com"},
    {"name": "Beam",            "base_url": "https://api.beam.cloud/v1",                                "docs": "beam.cloud/dashboard"},
    
    # Enterprise
    {"name": "Azure OpenAI",    "base_url": "https://YOUR_RESOURCE.openai.azure.com/openai/v1",     "docs": "azure.com"},
    {"name": "AWS Bedrock",     "base_url": "https://bedrock-runtime.{region}.amazonaws.com",         "docs": "aws.amazon.com/bedrock"},
    {"name": "Vertex AI",       "base_url": "https://{location}-aiplatform.googleapis.com/v1",       "docs": "cloud.google.com/vertex-ai"},
    
    # Specialized
    {"name": "Writer",          "base_url": "https://api.writer.com/v1",                               "docs": "writer.com"},
    {"name": "Aleph Alpha",     "base_url": "https://api.aleph-alpha.com/v1",                        "docs": "aleph-alpha.com"},
    {"name": "Nomic",          "base_url": "https://api-atlas.nomic.ai/v1",                          "docs": "nomic.ai"},
    
    # Open AI Compatible
    {"name": "Custom / Other",  "base_url": "",                                                        "docs": ""},
]

VERIFIED_OPENROUTER_MODELS = [
    "openrouter/auto",
    "meta-llama/llama-3.3-70b-instruct:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "google/gemma-3-27b-it:free",
    "microsoft/phi-4:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "qwen/qwen2.5-coder-7b-instruct:free",
    "deepseek/deepseek-r1:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
]

VERIFIED_GROQ_MODELS = [
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "gemma2-9b-it",
    "mixtral-8x7b-32768",
]

VERIFIED_OLLAMA_MODELS = [
    "llama3.2",
    "llama3.1",
    "qwen2.5-coder",
    "codellama",
    "mistral",
    "phi3",
]

SYSTEM_PROMPT = """You are HelloChusquis, an autonomous terminal AI agent with full system access. You execute tasks end-to-end without asking unnecessary questions.

## Core Principles
- **Act, don't describe**: Never say "I would do X" — just do X.
- **End-to-end execution**: Complete the full task in one response when possible.
- **Silent on success**: Don't narrate each step. Show results, not process.
- **Absolute paths always**: /Users/name/file.txt not ./file.txt
- **Real outputs only**: Never fake file contents, command results, or API responses.
- **Fail loudly**: If something breaks, say exactly what failed and why.

## Decision Framework
Before responding, ask yourself:
1. Does this need a tool? → Use it immediately, don't describe it.
2. Is this a multi-step task? → Generate a plan, execute it fully.
3. Did a step fail? → Try an alternative approach before giving up.
4. Is the user asking for a file? → Create the real file, don't paste content.

## Tools

### shell
Execute terminal commands. Use for: git, npm, pip, brew, system info, scripts, compilation.
```shell
shell: git log --oneline -10
```

### code  
Execute Python in a sandboxed environment. Use for: data processing, calculations, algorithms, JSON manipulation, testing logic.
```code
import json
print(json.dumps({"status": "ok"}, indent=2))
```

### files
Full filesystem access.
```files
action: read|write|delete|list|create_dir
path: /absolute/path
content: "only for write action"
```

## Plugins

### browser
Full browser automation via Playwright. Human-like mouse movement enabled.
Actions: goto, click, type, screenshot, extract_text, scroll, wait, back, forward, refresh
```browser
action: goto
url: https://example.com
```

### search
DuckDuckGo lite web search. You only have access to DuckDuckGo lite for web search. Do not attempt to use Google, Brave, or any paid search. If asked to search, use the search tool which uses DuckDuckGo.
```search
query: "search terms"
num_results: 5
```

### weather
```weather
city: Barcelona
```

### stocks / crypto
```stocks
symbol: AAPL
```
```crypto
action: price
coin: bitcoin
```

### pdf / docx
Generate real documents. Never paste content as text when user asks for a file.
```pdf
path: /absolute/path/output.pdf
content: "# Title\n\nBody text"
```

### calculator
```calculator
expression: "compound_interest(1000, 0.05, 10)"
```

### worldclock / currency
```worldclock
zones: ["America/New_York", "Europe/Madrid"]
```
```currency
from: USD
to: EUR  
amount: 100
```

## Multi-Step Task Execution
For complex tasks:
1. Generate a numbered plan
2. Execute each step sequentially
3. Pass outputs from one step as inputs to the next
4. If a step fails, adapt — don't abort the whole plan
5. Summarize what was accomplished at the end

## Error Recovery
- Tool fails → try alternative tool
- File not found → check if path exists first with files list
- API error → retry once, then explain the issue
- Permission denied → suggest sudo or alternative path

## Output Format
- Code: always in fenced blocks with language tag
- Files created: show the path, not the full content
- Long outputs: summarize, offer to show full output
- Errors: exact error message + what you tried + next step

## Memory & Context
You have access to conversation history summaries. Use them — never ask for information you already have. Reference past context naturally without announcing it.

## Plugin Not Available?
If user needs a capability you don't have: "I don't have a [X] plugin installed. Want me to build one?" Then build it if they say yes."""

def fetch_available_models(base_url: str, api_key: str) -> list[str]:
    base = base_url.rstrip("/")
    if "openrouter.ai" in base:
        return VERIFIED_OPENROUTER_MODELS
    if "groq.com" in base:
        return VERIFIED_GROQ_MODELS
    if "ollama.com" in base:
        return VERIFIED_OLLAMA_MODELS

    try:
        with httpx.Client(timeout=10) as client:
            r = client.get(
                f"{base}/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            r.raise_for_status()
            data = r.json()
            models = [m["id"] for m in data.get("data", data.get("models", []))]
            return sorted(models) if models else []
    except Exception:
        return []


def pick_provider() -> dict:
    table = Table(show_header=False, box=None, padding=(0, 2))
    for i, p in enumerate(KNOWN_PROVIDERS):
        table.add_row(
            f"[cyan]{i+1}[/cyan]",
            f"[bold]{p['name']}[/bold]",
            f"[dim]{p['docs']}[/dim]"
        )
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
        return Prompt.ask("  Model name", default="llama-3.3-70b-versatile")


def run_setup():
    console.print(Panel(
        "[bold #f5a623]HelloChusquis Setup[/bold #f5a623]\n"
        "[dim]Configure your AI providers[/dim]\n\n"
        "[yellow]⚠ Recommended: add at least 2 providers for fallback.[/yellow]",
        expand=False
    ))

    console.print("\n[dim]Tip: Start with Groq (fastest, free) then OpenRouter as fallback.[/dim]\n")

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

        console.print(f"  [#5eb97e]✓[/#5eb97e] Added: [bold]{provider_info['name']}[/bold] → [cyan]{model}[/cyan]")
        priority += 1

        if priority == 2:
            add_more = Confirm.ask("\n  Add another provider? [yellow](recommended)[/yellow]", default=True)
        else:
            add_more = Confirm.ask("\n  Add another provider?", default=False)

        if not add_more:
            if priority == 2:
                console.print("  [yellow]⚠ Only one provider. If it fails, HelloChusquis will stop.[/yellow]")
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

    config = {
        "providers": providers,
        "settings": {
            "provider_reset_hours": reset_hours,
            "max_retries": 3,
            "timeout_seconds": 15,
            "workspace_dirs": [workspace],
            "memory_retention_days": retention_days,
        },
        "agent": {
            "system_prompt": SYSTEM_PROMPT
        }
    }

    CONFIG_PATH.write_text(yaml.dump(config, allow_unicode=True, sort_keys=False))
    console.print(f"\n[#5eb97e]✓ Config saved to {CONFIG_PATH}[/#5eb97e]")
    return config


def run_quick_setup() -> dict:
    """Quick 60-second setup for first-time users."""
    from rich.prompt import Prompt
    from rich.console import Console

    console = Console()

    console.print(Panel(
        "[bold #f5a623]Welcome to HelloChusquis![/bold #f5a623]",
        expand=False
    ))

    console.print("\n[bold]Choose your AI provider:[/bold]\n")
    console.print("[#667eea]1.[/#667eea] OpenRouter - openrouter.ai/keys (recommended)")
    console.print("[#667eea]2.[/#667eea] Groq - console.groq.com/keys")
    console.print("[#667eea]3.[/#667eea] Ollama (local, no API key needed)\n")

    choice = Prompt.ask("[bold>Select option (1-3)[/bold]", default="1")

    if choice == "3":
        config = {
            "providers": [{
                "name": "ollama",
                "base_url": "http://localhost:11434/v1",
                "api_key": "ollama",
                "model": "llama3",
                "priority": 1,
            }],
            "settings": {
                "provider_reset_hours": 1,
                "max_retries": 3,
                "timeout_seconds": 120,
                "workspace_dirs": [str(Path.home() / ".hellochusquis" / "workspace")],
                "memory_retention_days": 30,
            },
            "agent": {
                "system_prompt": SYSTEM_PROMPT
            }
        }
    else:
        providers_config = {
            "1": {
                "name": "openrouter",
                "base_url": "https://openrouter.ai/api/v1",
                "model": "openrouter/auto",
            },
            "2": {
                "name": "groq",
                "base_url": "https://api.groq.com/openai/v1",
                "model": "llama-3.1-8b-instant",
            },
        }
        selected = providers_config.get(choice, providers_config["1"])
        console.print(f"\n[dim]Get a free API key at: [/dim]")
        if choice == "1":
            console.print("[dim]openrouter.ai/keys[/dim]")
        else:
            console.print("[dim]console.groq.com/keys[/dim]")

        api_key = Prompt.ask("[bold]Paste your API key[/bold]", password=True)

        config = {
            "providers": [{
                **selected,
                "api_key": api_key,
                "priority": 1,
            }],
            "settings": {
                "provider_reset_hours": 1,
                "max_retries": 3,
                "timeout_seconds": 15,
                "workspace_dirs": [str(Path.home() / ".hellochusquis" / "workspace")],
                "memory_retention_days": 30,
            },
            "agent": {
                "system_prompt": SYSTEM_PROMPT
            }
        }

    config_dir = Path.home() / ".hellochusquis"
    config_dir.mkdir(parents=True, exist_ok=True)
    workspace_path = config_dir / "workspace"
    workspace_path.mkdir(parents=True, exist_ok=True)
    config["settings"]["workspace_dirs"] = [str(workspace_path)]

    config_path = config_dir / "config.yaml"
    config_path.write_text(yaml.dump(config, allow_unicode=True, sort_keys=False))
    console.print(f"\n[#5eb97e]✓ Ready. Starting HelloChusquis...[/#5eb97e]")
    console.print(f"[dim]Config saved to: {config_path}[/dim]")
    return config


def ensure_config(quick: bool = False, full: bool = False) -> dict:
    # Busca config en varias ubicaciones posibles
    possible_paths = [
        Path("config.yaml"),
        Path.home() / "config.yaml",
        Path.home() / ".hellochusquis" / "config.yaml",
    ]

    for path in possible_paths:
        if path.exists():
            with open(path) as f:
                config = yaml.safe_load(f)
            # Actualiza system prompt si es viejo
            if "agent" not in config:
                config["agent"] = {"system_prompt": SYSTEM_PROMPT}
            elif len(config["agent"].get("system_prompt", "")) < 100:
                config["agent"]["system_prompt"] = SYSTEM_PROMPT
            return config

    # No config found - use quick setup by default, or full if requested
    if full:
        console.print("[yellow]No config found. Running full setup...[/yellow]\n")
        return run_setup()
    else:
        console.print("[yellow]No config found. Running quick setup...[/yellow]\n")
        return run_quick_setup()


def edit_config(section: str = None):
    """Edit configuration interactively."""
    config = ensure_config()
    
    console.print(Panel(
        "[bold #f5a623]HelloChusquis Config[/bold #f5a623]\n"
        "[dim]Update your configuration[/dim]",
        expand=False
    ))
    
    if section == "providers" or section is None:
        console.print("\n[bold cyan]Providers Configuration[/bold cyan]")
        providers = config.get("providers", [])
        
        # Edit each provider
        for i, p in enumerate(providers):
            console.print(f"\n[bold]Provider #{i+1}: {p['name']}[/bold]")
            
            name = Prompt.ask(f"  Name [{p.get('name', '')}]", default=p.get("name", ""))
            base_url = Prompt.ask(f"  Base URL [{p.get('base_url', '')}]", default=p.get("base_url", ""))
            current_key = p.get("api_key", "")
            api_key_label = "***" + current_key[-4:] if current_key else ""
            api_key = Prompt.ask(f"  API Key [{api_key_label}]", default="")
            if not api_key:
                api_key = current_key
            model = Prompt.ask(f"  Model [{p.get('model', '')}]", default=p.get("model", ""))
            
            providers[i] = {
                "name": name,
                "base_url": base_url,
                "api_key": api_key,
                "model": model,
                "priority": p.get("priority", i + 1),
            }
        
        # Add new provider
        add_new = Confirm.ask("\n  Add another provider?", default=False)
        priority = len(providers) + 1
        while add_new:
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
            priority += 1
            add_new = Confirm.ask("  Add another?", default=False)
        
        config["providers"] = providers
    
    if section == "api-keys" or section is None:
        console.print("\n[bold cyan]API Keys[/bold cyan]")
        providers = config.get("providers", [])
        for i, p in enumerate(providers):
            current_key = p.get("api_key", "")
            api_key_label = "***" + current_key[-4:] if current_key else ""
            console.print(f"  {p['name']}: [{api_key_label}]")
            try:
                new_key = input(f"  Enter new key for {p['name']} (press Enter to keep current): ")
            except EOFError:
                new_key = ""
            if new_key:
                providers[i]["api_key"] = new_key
                console.print(f"    ✓ Updated")
            else:
                console.print(f"    ✓ Kept existing")
        config["providers"] = providers
    
    if section == "settings" or section is None:
        console.print("\n[bold cyan]Settings[/bold cyan]")
        settings = config.get("settings", {})
        
        reset_hours = IntPrompt.ask(
            "  Reset exhausted providers after how many hours?",
            default=settings.get("provider_reset_hours", 1)
        )
        
        retention_days = IntPrompt.ask(
            "  Delete old sessions after how many days?",
            default=settings.get("memory_retention_days", 30)
        )
        
        workspace = Prompt.ask(
            "  Default workspace directory",
            default=settings.get("workspace_dirs", [str(Path.home() / "workspace")])[0]
        )
        
        config["settings"] = {
            "provider_reset_hours": reset_hours,
            "max_retries": 3,
            "timeout_seconds": 15,
            "workspace_dirs": [workspace],
            "memory_retention_days": retention_days,
        }
    
    CONFIG_PATH.write_text(yaml.dump(config, allow_unicode=True, sort_keys=False))
    console.print(f"\n[#5eb97e]✓ Config saved to {CONFIG_PATH}[/#5eb97e]")
    return config


def show_config():
    """Show current configuration with masked API keys."""
    config = ensure_config()
    
    console.print(Panel(
        "[bold #f5a623]HelloChusquis Configuration[/bold #f5a623]",
        expand=False
    ))
    
    providers = config.get("providers", [])
    console.print("\n[bold cyan]Providers:[/bold cyan]")
    for p in providers:
        api_key = p.get("api_key", "")
        masked_key = "***" + api_key[-4:] if len(api_key) > 4 else "***"
        console.print(f"  • {p.get('name', 'Unknown')}")
        console.print(f"    Model: {p.get('model', 'N/A')}")
        console.print(f"    API Key: {masked_key}")
    
    settings = config.get("settings", {})
    console.print("\n[bold cyan]Settings:[/bold cyan]")
    console.print(f"  • Reset after: {settings.get('provider_reset_hours', 1)} hours")
    console.print(f"  • Memory retention: {settings.get('memory_retention_days', 30)} days")
    console.print(f"  • Workspace: {settings.get('workspace_dirs', ['N/A'])[0]}")
    console.print(f"  • Timeout: {settings.get('timeout_seconds', 15)} seconds")