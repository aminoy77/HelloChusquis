# HelloChusquis v1.4.3

**HelloChusquis** is an AI terminal agent with chat interface, web search, file management, code execution, and multiple AI integrations. 

![HelloChusquis Demo](demo.gif)

## What's New in v1.4.3

- **Rate Limiting** — API endpoints protected with per-IP rate limits (30 req/min)
- **SSE Streaming** — Real-time streaming responses via Server-Sent Events
- **Smart History Compression** — Intelligent token-based context management (100 entries, auto-compress)
- **Structured Logging** — JSON logs with rotation to `~/.hellochusquis/logs/`
- **Health Endpoints** — `/health`, `/health/ready`, `/health/live` for monitoring
- **Web UI Auth** — Optional token-based authentication via `HELLOCHUSQUIS_API_KEY` env var
- **CLI --port/--host** — `hellochusquis api --port 9000 --host 127.0.0.1`
- **Graceful Shutdown** — SIGTERM/SIGHUP handlers save session before exit
- **64 Unit Tests** — Coverage for history, cache, rate limiter, functions, DB memory
- **Bug Fixes** — Session persistence (json.dumps), config path, Ollama detection, missing dependencies

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
*Built with ❤️ by aminoy77 and the HelloChusquis community.*
