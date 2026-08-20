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
- **Secure-by-default Web UI** — the web interface requires an API key by default, including on localhost
- **Recoverable HTTP Startup** — API and web servers remain live before setup and expose readiness instead of blocking on prompts
- **Isolated HTTP Sessions** — each client session receives separate agent context and history, with bounded LRU retention
- **Human Approval Gate** — HTTP agents stop high-impact actions such as shell execution, file mutation, external writes, MCP calls, and browser submissions until the session owner confirms them
- **Serialized Session Turns** — a session processes one chat request at a time, preventing concurrent requests from interleaving context or tool state; retry a `409` response after the active turn ends
- **Persistent Approval Audit** — requested, decided, and executed high-impact actions are retained per HTTP session with redacted arguments and can be inspected after a runtime reload; closed HTTP sessions are pruned to the 200 most recent records
- **Bounded Rate Limiting** — per-client request windows cap retained client state at 10,000 entries, reject invalid settings, and clean up without allocating state for read-only limit checks
- **Protected Administrative Operations** — runtime reloads allow at most 3 requests per minute per client, session-scoped provider updates allow 15, and model discovery allows 30 requests with only 5 forced remote refreshes; excess requests receive a `429` response with a `Retry-After` header
- **Safe Learning Persistence** — feedback is capped at 10 submissions per minute per client with a 500-character request bound; local learning writes are serialized, atomic, and retained with owner-only file permissions
- **Safe HTTP Error Contracts** — unavailable runtimes, failed reloads, approval conflicts, and execution failures return stable public messages while detailed diagnostics remain confined to server logs
- **Global Request Bounds** — API and web reject declared or streamed request bodies larger than 1 MiB with a `413` response before parsing, while normal requests retain their existing contracts
- **Offline Integration Contracts** — `doctor --contracts` verifies the import and local entry-point contract of every bundled external integration without calling third-party services

## Quick Start

```bash
pip install hellochusquis
hellochusquis
```

## Web Interface

```bash
hellochusquis web

# The first launch creates a local API key; supply it in the web UI.
cat ~/.hellochusquis/api_key.txt

# Or set your own key before starting the server.
HELLOCHUSQUIS_API_KEY=your-secret-key hellochusquis web
```

Then open http://localhost:7272. The web UI is authenticated by default. Only for an intentionally isolated local development session may you disable it with `HELLOCHUSQUIS_AUTH=0`.

## REST API

```bash
hellochusquis api --port 8080
export HC_TOKEN="$(cat ~/.hellochusquis/api_key.txt)"

# Regular request with an explicit isolated conversation session
curl -X POST http://localhost:8080/chat \
  -H "Authorization: Bearer $HC_TOKEN" \
  -H "X-HelloChusquis-Session: my-session" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "stream": false}'

# Streaming (SSE)
curl -X POST http://localhost:8080/chat \
  -H "Authorization: Bearer $HC_TOKEN" \
  -H "X-HelloChusquis-Session: my-session" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "stream": true}'

# Health and readiness checks
curl http://localhost:8080/health
curl http://localhost:8080/health/ready

# After changing providers with the setup CLI, reload configuration without restart
curl -X POST http://localhost:8080/runtime/reload \
  -H "Authorization: Bearer $HC_TOKEN"

# Inspect high-impact actions pending for your current session
curl http://localhost:8080/approvals \
  -H "Authorization: Bearer $HC_TOKEN" \
  -H "X-HelloChusquis-Session: my-session"

# Inspect the redacted, persistent approval audit for the same session
curl 'http://localhost:8080/audit?limit=50' \
  -H "Authorization: Bearer $HC_TOKEN" \
  -H "X-HelloChusquis-Session: my-session"

# Approve and execute exactly one pending action. Replaying the same request fails.
curl -X POST http://localhost:8080/approvals/APPROVAL_ID \
  -H "Authorization: Bearer $HC_TOKEN" \
  -H "X-HelloChusquis-Session: my-session" \
  -H "Content-Type: application/json" \
  -d '{"approve": true}'
```

High-impact calls issued through HTTP require approval by default. Approval requests are **session-local**, expire after five minutes, are consumed before execution, and redact credential-like fields from the client view. Local terminal use remains interactive.

## Integration Diagnostics

```bash
# Offline only: imports every integration exposed by the agent and checks its callable entry point.
# No provider credentials, network calls, or tool actions are used.
hellochusquis doctor --contracts
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
--port PORT          # Port for API/web server (default: 8080/7272)
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
HELLOCHUSQUIS_API_KEY=your-key    # API key required by web/API clients
HELLOCHUSQUIS_AUTH=0              # Disable web auth only for isolated local development
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
core/runtime.py  → Recoverable startup and bounded isolated HTTP sessions
core/approvals.py → Expiring, session-local, replay-safe human approvals
core/integration_contracts.py → Offline structural diagnostics for bundled integrations
web/server.py    → Authenticated FastAPI web interface
api/main.py      → Authenticated REST API with rate limiting
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
