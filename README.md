# HelloChusquis

A powerful terminal AI agent built in Python.

## Features
- Execute terminal commands
- Read, write, create and delete files in your workspace
- Execute Python code
- Multiple AI providers with automatic fallback
- Persistent memory between sessions
- `/status` — check provider status
- `/clear` — clear conversation history

## Supported Providers
OpenRouter, Ollama Cloud, Anthropic, OpenAI, Gemini, Groq, xAI, Perplexity, Qwen, MiniMax, Mistral, DeepSeek, Cohere, Together AI, Fireworks, Novita, and more.

## Install
```bash
git clone https://github.com/aminoy77/HelloChusquis
cd HelloChusquis-main
pip install -e .
```

## Run
```bash
hellochusquis
```

First run will ask you to configure your providers.
Recommended: add at least 2 providers for fallback.

## Commands
| Command | Description |
|---|---|
| `/status` | Show provider status |
| `/clear` | Clear conversation history |
| `exit` | Exit and save memory |
