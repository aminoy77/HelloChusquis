# HelloChusquis 🧠✨ v2.0

**HelloChusquis** is an advanced, self-improving AI terminal agent built in Python. With 60+ integrations, skill system, and auto-tool-builder.

## 🚀 What's New in v2.0

- **60+ AI Providers** - Including Chinese, European, Enterprise providers
- **Auto-Tool-Builder** - Run `/tool add <name>` to create new integrations
- **Skill System** - Reusable workflows with `/skill` commands
- **MCP Support** - Model Context Protocol for external tools
- **Background Tasks** - Long-running processes management
- **Smart Integration Suggestions** - Proposes building tools when needed

## ⚡ Quick Start

```bash
pip install hellochusquis
hellochusquis
```

## 🔧 Tool Builder

Create new integrations on-the-fly:

```bash
hellochusquis tool add stripe   # Creates Stripe integration
hellochusquis tool add custom # Creates custom API integration
```

## 🌐 Web Interface

```bash
hellochusquis web
```

## 📦 Integrations (60+)

| Category | Tools |
|----------|-------|
| Payments | Stripe, Square, Plaid, PayPal |
| Communication | Twilio, SendGrid, Resend, Brevo, Intercom |
| DevOps | Vercel, Supabase, Sentry, Datadog, PagerDuty |
| CRM/Marketing | HubSpot, Shopify, Mailchimp, Airtable, Clerk |
| CMS | Contentful, Sanity |
| Search | Algolia |
| Media | Cloudinary |
| Analytics | PostHog, LaunchDarkly |
| Automation | n8n, Pipedream, Retool, Workato, Make |
| Databases | PostgreSQL, MongoDB, Upstash |
| Meetings | Calendly, Zoom |
| Project | Linear, ClickUp, Jira |
| Code | GitHub, Bitbucket |

## 🤖 Skills

Skills are reusable workflows:

```python
# skills/code_review.json
{
  "name": "code_review",
  "actions": [
    {"type": "shell", "command": "ruff check {file}"},
    {"type": "shell", "command": "mypy {file}"}
  ]
}
```

## 📚 Documentation

- [README](README.md) - Full documentation
- [Examples](examples/) - Usage examples
- [Docs](docs/) - Landing page

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 License

MIT License. See [LICENSE](LICENSE).

---

*Built with ❤️ by aminoy77 and the HelloChusquis community.*