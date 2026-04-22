# HelloChusquis 🧠✨ v1.0

**HelloChusquis** is an advanced, self-improving AI terminal agent built in Python. Designed for developers and power-users, it seamlessly integrates with your terminal to automate complex tasks, manage files, execute code, and even build its own tools on demand.

## 🚀 What's New in v1.0

- **REST API** - Programmatic access to HelloChusquis
- **Streaming Responses** - Real-time AI output (beta)
- **Code Analysis** - Built-in ESLint, Black, Ruff, MyPy
- **Linear Integration** - Project management
- **Intelligent Caching** - Faster repeated queries
- **Improved Web UI** - Copy, like/dislike, config panel

## ⚡ Quick Start

```bash
pip install hellochusquis
hellochusquis
```

## 🌐 Web Interface

```bash
hellochusquis web
```

## 🔧 CLI Options

```bash
hellochusquis --profile safe    # Enhanced security
hellochusquis --profile aggressive  # No security checks
```

## 📦 Integrations

| Category | Tools |
|----------|-------|
| Code | GitHub, Code Analysis (ESLint, Black, Ruff, MyPy) |
| Communication | Slack, Discord, Twitter/X, Gmail |
| DevOps | Docker, AWS, Jira, Linear |
| Data | PostgreSQL, MongoDB |
| Productivity | Google Calendar, Notion, Spotify |

## 🔌 REST API

Start the API server:

```bash
hellochusquis api --port 8080
```

Endpoints:
- `POST /chat` - Send a message
- `GET /status` - Provider status
- `POST /feedback` - Send feedback
- `GET /history` - Conversation history

## 📚 Documentation

- [README](README.md) - Full documentation
- [Examples](examples/) - Usage examples
- [Plugins](https://github.com/aminoy77/HelloChusquis-plugins) - Plugin registry

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 License

MIT License. See [LICENSE](LICENSE).

---

*Built with ❤️ by aminoy77 and the HelloChusquis community.*