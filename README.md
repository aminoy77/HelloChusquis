# HelloChusquis 🧠✨ v1.3

**HelloChusquis** is an advanced AI terminal agent with 120+ integrations, voice support, and auto-tool-builder.

## 🚀 What's New in v1.3

- **120+ Integrations** - Every popular API and service
- **Voice I/O** - Speak and listen in the web interface (12+ languages)
- **Auto-Tool-Builder** - Create integrations on-the-fly with `/tool add`
- **Smart Suggestions** - When you ask for a missing tool, it offers to build it

## ⚡ Quick Start

```bash
pip install hellochusquis
hellochusquis
```

## 🌐 Web Interface with Voice

```bash
hellochusquis web
```

Then open http://localhost:8000

### Voice Controls:
- 🎤 Click to enable **voice input** - speaks and converts to text
- 🔊 Click to enable **voice output** - agent speaks responses
- 🌐 Select language from dropdown (Auto-detect, English, Spanish, French, etc.)
- Press **V** for voice input, **S** for voice output

## 🔧 Command Reference

### Core Commands:
```
hellochusquis              # Start interactive chat
hellochusquis web          # Open web interface
hellochusquis api --port 8080  # Start REST API
hellochusquis tool add <name>  # Build new integration
hellochusquis install <plugin> # Install plugin
hellochusquis plugins          # List installed plugins
hellochusquis cache           # Clear cache
```

### In-Chat Commands:
```
/clear      # Clear conversation history
/status    # Show provider status
/help      # Show available tools
```

## 🔌 REST API

```bash
# Start server
hellochusquis api --port 8080

# Chat endpoint
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
```

Endpoints:
- `POST /chat` - Send message
- `GET /status` - Provider status
- `POST /clear` - Clear history

## 📦 Integrations (120+)

### Payments & Banking
Stripe, Square, Plaid, PayPal, Braintree, Adyen, GoCardless

### Communication
Twilio, SendGrid, Resend, Brevo, Mailgun, Postmark, Intercom, Front

### CRM & Marketing
HubSpot, Salesforce, Pipedrive, Close, ActiveCampaign, Drip, ConvertKit, Mailchimp, Airtable, Coda

### Support
Freshdesk, Zendesk, Intercom, HelpScout

### DevOps & Cloud
Vercel, Supabase, AWS, DigitalOcean, Cloudflare, Heroku, Netlify, Railway, Render, Neon, PlanetScale, Upstash, Redis

### Monitoring
Datadog, Sentry, PagerDuty, New Relic, Grafana, Prometheus, Bugsnag, Rollbar, Hotjar, FullStory

### Analytics
PostHog, Mixpanel, Amplitude, Segment, Heap, Google Analytics, Plausible

### CMS & Content
Contentful, Sanity, Strapi, Ghost, Webflow, Prismic, Contentstack

### Forms & Surveys
Typeform, Jotform, Paperform, HubSpot Forms

### Video & Media
Zoom, Daily, Loom, Vimeo, Mux, Cloudinary, imgix

### Design & Collaboration
Figma, Miro, Canva, Framer, Loom

### Database
PostgreSQL, MongoDB, MySQL, Redis, Supabase, PlanetScale, Neon, CockroachDB, ClickHouse

### Email Marketing
Mailchimp, ConvertKit, ActiveCampaign, GetResponse, Brevo, Drip

### SMS & Notifications
Twilio, Plivo, MessageBird, Pushover, OneSignal, Firebase, Pusher, Ably

### Project Management
Linear, Jira, Asana, Trello, ClickUp, Todoist, Notion, Monday

### Automation
n8n, Pipedream, Make, Zapier, Workato, Retool

## 🤖 Voice Features

### Web Interface Voice:
- **Input**: Click 🎤 or press V - speaks and converts to text automatically
- **Output**: Click 🔊 or press S - agent speaks responses
- **Language**: Select from dropdown (12+ languages)
- **Auto-detect**: Uses browser language by default

### Supported Languages:
🌐 Auto-detect, English, Español, Français, Deutsch, Italiano, Português, 日本語, 한국어, 中文, Русский, العربية

### Tips for Voice:
- Use Chrome/Edge/Safari for best results
- Allow microphone permissions when prompted
- Select "Auto-detect" for automatic language recognition

## 🔧 Auto-Tool Builder

Create new integrations instantly:

```bash
hellochusquis tool add stripe
```

The tool builder will ask for:
- Integration name
- Description
- API type (REST, GraphQL, etc.)
- Actions available

## 📚 Documentation

- [README](README.md) - This file
- [docs/index.html](../docs/index.html) - Landing page
- [examples/README.md](../examples/README.md) - Usage examples

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 License

MIT License.

---

*Built with ❤️ by aminoy77 and the HelloChusquis community.*