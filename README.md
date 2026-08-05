# HelloChusquis v5.0

**HelloChusquis** is an AI terminal agent with a full-screen TUI, web search, file management, code execution, and multiple AI integrations. 

![HelloChusquis Demo](demo.gif)

## What's New in v5.0

- **54-Provider Catalog** — Expanded from 35 to 54 AI providers across 9 categories (Major, European, Chinese, AI Platforms, Open Source, Local, Enterprise, Specialized, Custom)
- **20 New Providers** — Cerebras, NVIDIA NIM, DeepInfra, SiliconFlow, Volcengine, Baidu Qianfan, Tencent Hunyuan, StepFun, Jina AI, FriendliAI, LM Studio, vLLM, Jan, AI21, TextCortex, Baseten, Modal, TextGen WebUI, LocalAI, AnythingLLM
- **Provider/Model Selection UI** — Full catalog browsing with grouped categories, paginated model lists, number or text search
- **Unified Setup Flow** — `run_quick_setup` and `run_setup` now use the full 54-provider catalog with model lists
- **SSE Streaming** — `/clear` and `/status` now return Server-Sent Events; `/chat/stream` for real-time responses
- **20+ New Tool Integrations** — GitHub, Discord, Stripe, Shopify, Notion, Twilio, HubSpot, Intercom, Mailchimp, MongoDB, PagerDuty, Datadog, ClickUp, Resend, Sanity, Vercel, and more
- **Security Hardening Round 2** — Block renamed fork bombs, 2-stage RCE patterns, `python -c` with dangerous imports, disk destruction commands, and more
- **Performance Improvements** — Flat write path for db_memory, vocab cache reuse, no per-query vocabulary rebuild
- **TUI Interface** — New `ui/tui.py` with 481 lines of rich terminal UI
- **Web UI Restructured** — Sidebar with Providers, Memory, Learnings panels; model dropdown population fix
- **Auth Opt-in** — `HELLOCHUSQUIS_AUTH` env var for optional authentication (disabled by default for local use)

## Quick Start

```bash
pip install hellochusquis
hellochusquis
```

## Web Interface

```bash
hellochusquis web
# Optional: set auth
HELLOCHUSQUIS_API_KEY=your-secret-key hellochusquis web
```

Then open http://localhost:8000

## REST API

```bash
hellochusquis api --port 8080

# Regular request
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'

# Streaming (SSE)
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "stream": true}'

# Health check
curl http://localhost:8080/health
```

## Command Reference

### Core Commands:
```
hellochusquis              # Start interactive chat
hellochusquis web          # Open web interface
hellochusquis api --port 8080 --host 0.0.0.0  # Start REST API
hellochusquis config       # Reopen setup wizard
hellochusquis config --show  # Show current config
hellochusquis config --api-keys  # Edit API keys
hellochusquis config --providers  # Edit providers
```

### CLI Flags:
```
--quick              # Quick setup with OpenRouter only
--full               # Full setup wizard with all providers
--port PORT          # Port for API/web server (default: 8080/8000)
--host HOST          # Host for API/web server (default: 0.0.0.0/127.0.0.1)
```

### Built-in Tools:
- **shell** - Execute terminal commands
- **code** - Run Python code
- **files** - Read/write files (read, write, delete, list, create_dir)
- **web_search** - Search the web via DuckDuckGo
- **browser** - Browser automation (navigate, click, type, screenshot)

### Available Integrations:
GitHub, Slack, Discord, Docker, Notion, AWS, Gmail, Jira, PostgreSQL, MongoDB, Stripe, Twilio, Supabase, Vercel, HubSpot, Shopify, Mailchimp, Airtable, Linear, Kubernetes, Terraform, and more.

## Environment Variables

```bash
HELLOCHUSQUIS_API_KEY=your-key    # Enable auth for web/API
HELLOCHUSQUIS_UNSAFE_MODE=1       # Skip security checks
HELLOCHUSQUIS_PROFILE=aggressive  # Skip safety reviews
DEBUG=1                           # Enable debug logging
```

## Architecture

```
main.py          → Interactive loop, task detection
core/agent.py    → LLM orchestration, tool dispatch
core/provider.py → Multi-provider pool with fallback
core/history.py  → Smart context compression
core/planner.py  → Multi-step task planning
core/db_memory.py → SQLite session persistence
core/logger.py   → Structured JSON logging
web/server.py    → FastAPI web interface
api/main.py      → REST API with rate limiting
tools/           → 130+ integration modules
```

## Testing

```bash
python -m unittest discover tests/
# or
python -m pytest tests/
```

## Documentation

- [README](README.md) - This file
- [docs/index.html](docs/index.html) - Web interface

## License

MIT License.

---
*Built with ❤️ by aminoy77*
