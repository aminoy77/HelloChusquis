# HelloChusquis

**🤖 A powerful Terminal AI Agent** with multi-provider fallback, plugins, persistent memory and auto-learning.

[![PyPI version](https://img.shields.io/pypi/v/hellochusquis.svg)](https://pypi.org/project/hellochusquis/)
[![GitHub stars](https://img.shields.io/github/stars/aminoy77/HelloChusquis.svg)](https://github.com/aminoy77/HelloChusquis/stargazers)
[![License](https://img.shields.io/github/license/aminoy77/HelloChusquis)](https://github.com/aminoy77/HelloChusquis/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)

---

An intelligent AI agent that lives in your terminal (and browser). Supports 15+ LLM providers, has a plugin system, persistent memory, learns from you, and can create real files.

## ✨ Features

- 🔄 **Smart Multi-Provider Fallback** — automatically switches when a provider fails or rate limits
- 🧩 **Plugin System** — install with one command, create your own easily
- 🧠 **Persistent Memory + Auto-learning** — remembers conversations and improves with feedback (`👍` / `👎`)
- 📋 **Task Planner** — breaks down complex tasks and executes them step by step
- 🌐 **Web Interface** — clean browser chat with sidebar
- 📄 **Real File Creation** — generates actual PDF and Word documents
- 🔍 **Browser Control** — search the web and extract content

## Supported Providers
OpenRouter, Groq, Anthropic Claude, OpenAI, Google Gemini, xAI Grok, Ollama, Perplexity, Mistral, DeepSeek, Qwen, and more.

## Installation

### Recommended
```bash
pip install hellochusquis
Alternative (one-click)
Bashcurl -sSL https://raw.githubusercontent.com/aminoy77/HelloChusquis/main/install.sh | bash
Quick Start
Bashhellochusquis          # Start terminal chat
hellochusquis web      # Start web interface<a href="http://localhost:8000" target="_blank" rel="noopener noreferrer nofollow"></a>
First run will guide you to add API keys. Add at least 2 providers for best experience.
Useful Commands

/plan <task> → Force planning mode
hellochusquis install weather → Install a plugin
👍 or + → Positive feedback (agent learns)
hellochusquis web → Open browser interface

Plugins
Bashhellochusquis install browser
hellochusquis install pdf
hellochusquis install stocks
hellochusquis install crypto
hellochusquis install docx
Explore all plugins → HelloChusquis Plugins
How it Works

Intelligent provider routing (prefers tool-calling models)
Task planning with user confirmation
Automatic conversation summarization and learning


License: MIT
Made with ❤️ for power users and AI enthusiasts
⭐ Star the repo if you like it!
