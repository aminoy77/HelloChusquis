# HelloChusquis

**🤖 A powerful Terminal AI Agent** built in Python with web interface, multi-provider fallback, plugin system, persistent memory, and auto-learning.

[![PyPI version](https://img.shields.io/pypi/v/hellochusquis)](https://pypi.org/project/hellochusquis/)
[![GitHub stars](https://img.shields.io/github/stars/aminoy77/HelloChusquis)](https://github.com/aminoy77/HelloChusquis/stargazers)
[![License](https://img.shields.io/github/license/aminoy77/HelloChusquis)](https://github.com/aminoy77/HelloChusquis/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)

---

An intelligent AI agent that lives in your terminal (and browser). It can execute commands, create real files (PDF, Word), control the browser, plan tasks, and learn from every conversation.

## ✨ Features

- 🤖 **Full AI Agent** — chat in terminal or browser with tool access
- 🔄 **Multi-provider fallback** — automatically switches providers when one fails
- 🧩 **Plugin system** — install plugins with one command, build your own
- 🧠 **Persistent memory** — remembers conversations and learns from them
- 📋 **Task Planner** — breaks down complex tasks and executes them step by step
- 🌐 **Web Interface** — beautiful chat in your browser
- 📄 **Real file generation** — creates actual PDF and Word documents
- 🔍 **Browser control** — search the web and extract content from pages

## Supported Providers
OpenRouter, Ollama, Anthropic Claude, OpenAI, Google Gemini, Groq, xAI (Grok), Perplexity, Qwen, Mistral, DeepSeek, Cohere, Together AI, Fireworks AI, and more.

## Installation

### Recommended (pip)
```bash
pip install hellochusquis
Other options
Bash# Clone from GitHub
git clone https://github.com/aminoy77/HelloChusquis.git
cd HelloChusquis
pip install -e .

# One-click installer
curl -sSL https://raw.githubusercontent.com/aminoy77/HelloChusquis/main/install.sh | bash
First Run
Bashhellochusquis
It will launch the setup wizard. It is recommended to add at least 2 providers for reliable fallback.
Usage
Bashhellochusquis          # Start terminal chat
hellochusquis web      # Start web interface (opens browser at http://localhost:8000)
Useful Commands

/help — Show all commands
/status — Check provider status
/plan <task> — Force planning mode
👍 or + — Give positive feedback (agent learns)
👎 or - — Give negative feedback
hellochusquis install weather — Install a plugin

Plugins
Bashhellochusquis install weather
hellochusquis install stocks
hellochusquis install browser
hellochusquis install pdf
hellochusquis install docx
hellochusquis install crypto
Browse all available plugins → HelloChusquis Plugins
Create your own plugin:
Bashhellochusquis build
Web Interface
Bashhellochusquis web
Opens a modern chat at http://localhost:8000 with sidebar showing providers, plugins, memory, and learned patterns.
How it Works

Smart Fallback — automatically uses the best available provider
Task Planner — plans complex tasks and asks for confirmation
Auto-learning — improves itself after every session based on your feedback

License
MIT
