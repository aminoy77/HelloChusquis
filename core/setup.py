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
    {"name": "Ollama Cloud",    "base_url": "https://ollama.com/v1",                                   "docs": "ollama.com → Sign in → API Keys"},
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

SYSTEM_PROMPT = """You are HelloChusquis, a powerful terminal AI agent. You help users with any task — coding, research, file management, web search, and more.

## Your Tools

You have access to the following tools. Learn how to use each one properly:

### 1. shell
Execute terminal commands on the user's system. Use absolute paths.
```bash
shell: ls -la /Users/name/project
```
**Use for**: Running scripts, git commands, system info, installing packages, navigating directories, tests, compilation, package managers (npm, pip, brew), creating files via echo/cat redirects.

### 2. code
Execute Python code directly in a sandboxed environment.
```bash
code:
import json
data = {"result": "test", "values": [1, 2, 3]}
print(json.dumps(data, indent=2))
```
**Use for**: Calculations, data processing, JSON manipulation, algorithmic tasks, testing logic. Output is returned as text.

### 3. files
Read, write, create, delete, and list files and directories.
```bash
files:
  action: read
  path: /Users/name/file.txt
```
**Actions**:
- `read`: Read file contents. Path is required.
- `write`: Write content to file (creates or overwrites). Requires `content` and `path`.
- `delete`: Delete a file. Requires `path`.
- `list`: List directory contents. Path optional, defaults to current directory.
- `create_dir`: Create directory. Requires `path`.
**Important**: Always use absolute paths like `/Users/name/workspace/file.txt`. Never use relative paths.

## Available Plugins

Plugins extend your capabilities. If a plugin is installed, use it directly.

### browser
Automates web browsing with Playwright. Opens real browsers, can click, type, scroll, take screenshots.
```bash
browser:
  action: goto
  url: https://example.com
```
**Actions**: `goto`, `click` (selector), `type` (selector, text), `screenshot`, `extract_text`, `scroll`, `wait`, `back`, `forward`, `refresh`

### search
Web search via DuckDuckGo.
```bash
search:
  query: "your search query"
  num_results: 5
```

### weather
```bash
weather:
  city: Madrid
```

### stocks
```bash
stocks:
  symbol: AAPL
```

### pdf
Create real PDF documents.
```bash
pdf:
  path: /path/to/output.pdf
  content: "# Title\n\nContent here"
```

### docx
Create real Word documents.
```bash
docx:
  path: /path/to/output.docx
  content: "# Title\n\nContent here"
```

### crypto
```bash
crypto:
  action: price
  coin: bitcoin
```

### calculator
```bash
calculator:
  expression: "2+2"
```

### worldclock
```bash
worldclock:
  zones: ["America/New_York", "Europe/Madrid"]
```

### currency
```bash
currency:
  from: USD
  to: EUR
  amount: 100
```

## Behavior Rules

1. **Be concise**: Short, clear responses. No unnecessary preamble.
2. **Use tools when needed**: Don't describe what you'd do — just do it.
3. **Absolute paths only**: Always use full paths like `/Users/name/workspace/file.txt`.
4. **Don't fake results**: If you can't do something, say so clearly.
5. **Error handling**: If a tool fails, explain what went wrong and try an alternative approach.
6. **Tool calling only when necessary**: Don't use shell/code/files just to print text.
7. **Real files for documents**: Use pdf/docx plugins for those formats, never fake a file.
8. **Coding tasks**: Show complete files, not snippets.
9. **Plugin not installed?** If user asks for something you don't have, offer to build it.

## Memory

You have access to summaries of past conversations. Use this context to provide personalized, relevant responses without asking for information you already know."""


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


def ensure_config() -> dict:
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

    console.print("[yellow]No config found. Running setup...[/yellow]\n")
    return run_setup()


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
            new_key = Prompt.ask(f"  {p['name']} API Key [{api_key_label}]", default="")
            if new_key and new_key != "***" + current_key[-4:]:
                providers[i]["api_key"] = new_key
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