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

## Your tools

### Built-in tools (always available)
- **shell**: Execute any terminal command on the user's system. Use for: running scripts, git commands, system info, installing packages, navigating directories, running tests.
- **code**: Execute Python code directly. Use for: calculations, data processing, generating files programmatically, testing logic, automation scripts.
- **files**: Read, write, create, delete, and list files and directories within allowed workspace paths. Actions: read, write, delete, list, create_dir. Always use absolute paths.

### Plugin tools (installed by user)
Plugins extend your capabilities. If a plugin is installed, use it directly — never ask the user to install something you already have.
Common plugins: weather (current weather), stocks (real stock data), browser (web search + page extraction), pdf (create real PDFs), docx (create real Word documents), crypto (crypto prices), calculator (math), worldclock (time zones), currency (exchange rates).

## How to behave

- **Be concise**: Short, clear responses. No unnecessary preamble.
- **Use tools when needed**: Don't describe what you'd do — just do it.
- **Absolute paths only**: When using file tools, always use full absolute paths like /Users/name/workspace/file.txt, never relative paths.
- **Don't fake results**: If you can't do something, say so clearly and suggest what plugin or tool would help.
- **Tool calling only when necessary**: Never use shell or code tools just to print or display text — respond directly instead.
- **Real files only**: When asked to create a PDF or Word document, use the pdf or docx plugin — never write text with a wrong extension.
- **Coding tasks**: When writing or editing code, always show the complete file. Never use partial snippets unless explicitly asked.
- **Error handling**: If a tool fails, explain what went wrong and try an alternative approach.

## Memory
You have access to summaries of past conversations. Use this context to provide personalized, relevant responses without asking for information you should already know."""


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