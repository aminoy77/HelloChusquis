# HelloChusquis v1.4.0

[![🚀 Launching on Uneed — May 7, 2026](https://img.shields.io/badge/Uneed-Launch_May_7_2026-667eea?style=flat&logo=rocket)](https://www.uneed.best/tool/hellochusquis)

**HelloChusquis** is an AI terminal agent with chat interface, web search, file management, code execution, and multiple AI integrations. 

![HelloChusquis Demo](demo.gif)

## What's New in v1.3.1

- **Fixed --api-keys** - Config command now correctly updates API keys
- **Config flags fixed** - --show, --api-keys, --providers, --quick, --full all work
- **Fixed Web Search** - Now uses reliable DuckDuckGo lite
- **Fixed Plan Tools** - Tools now work correctly in multi-step plans

## Quick Start

```bash
pip install hellochusquis
hellochusquis
```

## Web Interface

```bash
hellochusquis web
```

Then open http://localhost:8000

## Command Reference

### Core Commands:
```
hellochusquis              # Start interactive chat
hellochusquis web          # Open web interface
hellochusquis api --port 8080  # Start REST API
hellochusquis config       # Reopen setup wizard
hellochusquis config --show  # Show current config
hellochusquis config --api-keys  # Edit API keys
hellochusquis config --providers  # Edit providers
```

### Built-in Tools:
- **shell** - Execute terminal commands
- **code** - Run Python code
- **files** - Read/write files (read, write, delete, list)
- **web_search** - Search the web via DuckDuckGo

### Available Integrations:
GitHub, Slack, Discord, Docker, Notion, AWS, Gmail, Jira, PostgreSQL, MongoDB, Stripe, Twilio, Supabase, Vercel, HubSpot, Shopify, Mailchimp, Airtable, and more.

## REST API

```bash
hellochusquis api --port 8080

curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
```

## Documentation

- [README](README.md) - This file
- [docs/index.html](docs/index.html) - Web interface

## License

MIT License.

---
*Built with ❤️ by aminoy77 and the HelloChusquis community.*