# HelloChusquis 🧠✨ v1.1.0

**HelloChusquis** is an advanced AI terminal agent with 150+ integrations, voice support, auto-tool-builder, browser automation, and 100+ built-in functions.

## 🚀 What's New in v1.1.0

- **Config Command** - `hellochusquis config` reopens setup wizard anytime
- **Browser Automation** - Control a real browser with human-like mouse movements
- **150+ Integrations** - Every popular API and service
- **Voice I/O** - Speak and listen in web interface (12+ languages)
- **Auto-Tool-Builder** - Create integrations with `hellochusquis build`
- **100+ Built-in Functions** - Time, hash, files, JSON, CSV, images, QR
- **5 Themes** - Dark, Light, Minimal, Ocean, Forest
- **Provider Config** - Configure API keys directly in web UI

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
- 🎤 Click to enable **voice input**
- 🔊 Click to enable **voice output**
- 🌐 Select language (12+ options)
- Press **V** for voice input, **S** for output

## 🔧 Command Reference

### Core Commands:
```
hellochusquis              # Start interactive chat
hellochusquis web          # Open web interface
hellochusquis api --port 8080  # Start REST API
hellochusquis config       # Reopen setup wizard
hellochusquis config --show  # Show current config (masked keys)
hellochusquis config --api-keys  # Edit only API keys
hellochusquis config --providers  # Edit only providers
hellochusquis build        # Build new plugin with AI
hellochusquis install     # Install plugin
hellochusquis plugins     # List plugins
hellochusquis cache       # Clear cache
```

### In-Chat Commands:
```
/clear      # Clear conversation history
/status    # Show provider status
/help      # Show available tools
```

## 🎨 Web UI Themes

- 🌙 Dark (default)
- ☀️ Light
- ⚫ Minimal
- 🌊 Ocean
- 🌲 Forest

### Web UI Features:
- ⚙️ Config panel with provider settings
- 😀 Emoji picker
- ⌨️ Keyboard shortcuts (Tab, C, ?, Esc)
- 📤 Export chat (JSON, Markdown, HTML)

## 📦 Integrations (150+)

### Payments & Banking
Stripe, Square, Plaid, PayPal, Braintree, Adyen, GoCardless

### Communication
Twilio, SendGrid, Resend, Brevo, Mailgun, Postmark, Intercom, Front

### CRM & Marketing
HubSpot, Salesforce, Pipedrive, Close, ActiveCampaign, Mailchimp, ConvertKit

### DevOps & Cloud
Vercel, Supabase, AWS, DigitalOcean, Cloudflare, Netlify, Railway, Render

### Social
GitHub, Discord, Slack, Telegram, LinkedIn, Twitter, Instagram, Facebook

### Productivity
Trello, Notion, Airtable, Asana, Linear, Monday, ClickUp, Google Sheets/Calendar

### Storage
Dropbox, Google Drive, Box, S3, Backblaze, Wasabi, Cloudflare R2

## ⚡ Built-in Functions (100+)

### Time & Date
`get_current_time`, `get_timestamp`, `calculate_date`, `date_add`

### Hash & Encode
`hash_string`, `base64_encode`, `url_encode`

### Files
`file_exists`, `file_size`, `list_directory`, `read_json`, `write_json`

### Data
`csv_to_json`, `json_to_csv`, `filter_json`, `sort_json`, `group_by`

### Images
`image_info`, `image_resize`, `image_thumbnail` (PIL)

### Web
`download_file`, `scrape_html`, `scrape_json`, `check_website`

### Browser Automation
`browser_open`, `browser_click`, `browser_type`, `browser_scroll`, `browser_screenshot`, `browser_search`, `browser_explore`

### Utilities
`generate_password`, `password_strength`, `qr_code`, `random_string`, `uuid`

## 🌐 Browser Automation

HelloChusquis can control a real browser with human-like mouse movements:

```bash
hellochusquis
# Then ask: "Open Chrome and search for Python tutorials"
```

### Browser Functions:
- **browser_open(url)** - Navigate to URL
- **browser_click(text="Submit")** - Click by text or CSS selector
- **browser_type(text, selector)** - Type into input fields
- **browser_scroll(direction, amount)** - Scroll up/down
- **browser_screenshot(path)** - Take screenshot
- **browser_search(query, engine)** - Search the web
- **browser_explore(url, task)** - Explore website for information

### Human-Like Mouse Movement:
The browser agent uses realistic mouse movements with:
- Non-linear paths with wobbles
- Occasional circular micro-movements
- Small jumps/bumps
- Variable speed and pauses
- Natural click timing

Perfect for:
- Filling surveys
- Automating web forms
- Research and data gathering
- Price comparisons
- Job applications

## 🛠️ Build Custom Plugins

```bash
hellochusquis build
```

Describe what you want to build, and AI will generate the integration!

## REST API

```bash
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

## 📚 Documentation

- [README](README.md) - This file
- [docs/index.html](../docs/index.html) - Landing page
```

## 🛠️ Build Custom Plugins

Create new plugins/integrations on-the-fly with AI:

```bash
hellochusquis build
```

The builder will ask you:
1. What do you want to build? (e.g., "Telegram bot", "Dropbox integration")
2. Plugin name

It will research the API, generate the code, test it, and save it to `~/.hellochusquis/plugins/`

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

Create new integrations instantly with AI:

```bash
hellochusquis build
```

The builder will ask for:
- What you want to build (e.g., "Telegram bot", "Dropbox integration")
- Plugin name

It will research the API, generate code, test it, and save it.

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