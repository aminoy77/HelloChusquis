# HelloChusquis

A powerful terminal AI agent built in Python with web interface, multi-provider fallback, plugin system, persistent memory, and auto-learning.

## Features

- 🔄 **Multi-provider fallback** — 19+ providers, switches automatically when one fails
- 🧩 **Plugin system** — install with one command, build your own with AI
- 🧠 **Persistent memory** — remembers past sessions and learns from them
- 📋 **Task planner** — detects complex tasks, plans, confirms, executes autonomously
- 🌐 **Web interface** — chat from your browser with live sidebar
- 🔍 **Browser control** — search the web, extract content from pages
- 📄 **Real file generation** — actual PDF and Word documents
- 📈 **Real stock data** — historical prices, volatility, moving averages
- 🔒 **Workspace permissions** — only accesses directories you allow
- 🤖 **Auto-learning** — gets better with every session

## Supported Providers

OpenRouter, Ollama Cloud, Anthropic Claude, OpenAI, Google Gemini, Groq, xAI (Grok), Perplexity, Qwen, MiniMax, Mistral, DeepSeek, Cohere, Together AI, Fireworks AI, Novita AI, Blackbox AI, Xiaomi MiMo, and more.

## Installation

### pip — recommended

```bash
pip install hellochusquis
```

### curl

```bash
curl -sSL https://raw.githubusercontent.com/aminoy77/HelloChusquis/main/install.sh | bash
```

### git clone

```bash
git clone https://github.com/aminoy77/HelloChusquis.git
cd HelloChusquis
pip install -e .
```

Requires Python 3.10+

## First Run

```bash
hellochusquis
```

Setup wizard launches automatically. Add at least 2 providers for fallback. Free tiers available on all major providers.

## Usage

```bash
hellochusquis          # Terminal chat
hellochusquis web      # Web interface at localhost:8000
```

## Chat Commands

| Command | Description |
|---|---|
| `/help` | Show available commands |
| `/status` | Show provider status |
| `/clear` | Clear conversation history |
| `/plan <task>` | Force planning mode |
| `👍` or `+` | Positive feedback |
| `👎` or `-` | Negative feedback |
| `exit` | Exit and save memory |

## Terminal Commands

```bash
hellochusquis install <plugin>     # Install a plugin
hellochusquis uninstall <plugin>   # Remove a plugin
hellochusquis plugins              # List installed plugins
hellochusquis build                # Build a new plugin with AI
hellochusquis learn                # Show learned patterns
hellochusquis web                  # Start web interface
```

## Plugins

```bash
hellochusquis install weather
hellochusquis install stocks
hellochusquis install browser
hellochusquis install pdf
hellochusquis install docx
hellochusquis install crypto
hellochusquis install calculator
hellochusquis install worldclock
hellochusquis install currency
```

All available plugins: [github.com/aminoy77/OpenManolo-plugins](https://github.com/aminoy77/OpenManolo-plugins)

### Build your own

```bash
hellochusquis build
```

The AI researches the API, writes the plugin, tests it, and asks if you want to submit it to the public registry.

## Web Interface

```bash
hellochusquis web
```

Opens at `http://localhost:8000` — same aesthetic as the landing page.

## Links

- Website: [aminoy77.github.io/HelloChusquis](https://aminoy77.github.io/HelloChusquis)
- PyPI: [pypi.org/project/hellochusquis](https://pypi.org/project/hellochusquis)
- Plugins: [github.com/aminoy77/OpenManolo-plugins](https://github.com/aminoy77/OpenManolo-plugins)

## License

MIT