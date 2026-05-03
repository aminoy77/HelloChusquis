# HelloChusquis v1.3.0

**HelloChusquis** is an AI terminal agent with chat interface, web search, file management, code execution, and multiple AI integrations. 

![HelloChusquis Demo](demo.gif)

## What's New in v1.3.0

- **Quick Setup** - First run shows simple 60-second setup with just one question for API key
- **Setup Flags** - `hellochusquis setup --quick` for quick reset, `--full` for full wizard
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