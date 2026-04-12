# HelloChusquis

A powerful terminal AI agent built in Python with web interface, multi-provider fallback, plugin system, persistent memory, and auto-learning.

## Features

- 🤖 **AI Agent** — chat in terminal or browser with full tool access
- 🔄 **Multi-provider fallback** — automatically switches between providers when one fails
- 🧩 **Plugin system** — install plugins with one command, build your own
- 🧠 **Persistent memory** — remembers past conversations and learns from them
- 📋 **Task planner** — detects complex tasks and executes them step by step
- 🌐 **Web interface** — chat from your browser with sidebar showing status
- 📄 **Real file creation** — generates real PDF and Word documents
- 🔍 **Browser control** — search the web and extract content from pages

## Supported Providers

OpenRouter, Ollama Cloud, Anthropic Claude, OpenAI, Google Gemini, Groq, xAI (Grok), Perplexity, Qwen, MiniMax, Mistral, DeepSeek, Cohere, Together AI, Fireworks AI, Novita AI, and more.

## Installation

### Option 1 — Download ZIP

1. Go to [github.com/aminoy77/HelloChusquis](https://github.com/aminoy77/HelloChusquis)
2. Click **Code → Download ZIP**
3. Unzip the file
4. Open terminal in the unzipped folder
5. Run:
```bash
pip install -e .
```

### Option 2 — Clone repo

```bash
git clone https://github.com/aminoy77/HelloChusquis.git
cd HelloChusquis
pip install -e .
```

## First Run

```bash
hellochusquis
```

First run will launch the setup wizard to configure your providers. It is recommended to add at least 2 providers for automatic fallback.

Get free API keys at:
- [openrouter.ai](https://openrouter.ai) — access 300+ models, many free
- [console.groq.com](https://console.groq.com) — fastest free tier
- [ollama.com](https://ollama.com) — cloud models

## Usage

### Terminal

```bash
hellochusquis          # Start chat in terminal
hellochusquis web      # Start web interface (opens browser)
```

### Chat Commands

| Command | Description |
|---|---|
| `/help` | Show available commands |
| `/status` | Show provider status |
| `/clear` | Clear conversation history |
| `/plan <task>` | Force planning mode for a task |
| `👍` or `+` | Positive feedback on last response |
| `👎` or `-` | Negative feedback on last response |
| `exit` | Exit and save memory |

### Terminal Commands

```bash
hellochusquis install      # Install a plugin
hellochusquis uninstall    # Remove a plugin
hellochusquis plugins              # List installed plugins
hellochusquis build                # Build a new plugin with AI
hellochusquis learn                # Show learned patterns and rules
hellochusquis web                  # Start web interface
```

## Plugins

Install plugins from the public registry:

```bash
hellochusquis install weather
hellochusquis install stocks
hellochusquis install browser
hellochusquis install pdf
hellochusquis install docx
hellochusquis install crypto
hellochusquis install calculator
hellochusquis install worldclock
```

Browse all available plugins at [github.com/aminoy77/OpenManolo-plugins](https://github.com/aminoy77/OpenManolo-plugins)

### Build your own plugin

```bash
hellochusquis build
```

The AI will research the API, write the plugin code, test it, and ask if you want to submit it to the public registry.

## Web Interface

```bash
hellochusquis web
```

Opens a web chat at `http://localhost:8000` with:
- Chat interface with tool call visualization
- Sidebar with provider status, installed plugins, memory stats, and learned patterns

## How it works

**Provider fallback** — if a provider hits rate limits or times out, HelloChusquis automatically switches to the next one. Providers that support tool calling are prioritized for tasks that need tools.

**Task planner** — for complex tasks, HelloChusquis generates a step-by-step plan, shows it to you for confirmation, then executes each step automatically.

**Memory** — at the end of each session, HelloChusquis summarizes the conversation and stores it. Next session it remembers what you discussed.

**Auto-learning** — after each session, the agent analyzes what worked and what didn't, and improves its behavior over time.

## License

MIT
