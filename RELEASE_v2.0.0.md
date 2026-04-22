# HelloChusquis v2.0.0 Release Notes

## 🚀 What's New in v2.0.0

This major release brings **60+ integrations**, the **Auto-Tool Builder**, and **skill system**.

### ✨ Major Features

#### 1. Auto-Tool Builder
Create new integrations on-the-fly:
```bash
hellochusquis tool add stripe   # Creates Stripe integration
hellochusquis tool add custom # Creates custom API integration
```

#### 2. Skills System
Reusable workflows that bundle multiple actions:
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

#### 3. Smart Integration Suggestions
When you ask for a tool that doesn't exist, HelloChusquis proposes to build it.

#### 4. MCP Support
Model Context Protocol for connecting to external AI tools and services.

#### 5. Background Tasks
Long-running process management.

---

### 📦 New Integrations (27 total)

**Payments & Banking:**
- Stripe, Square, Plaid

**Communication:**
- Twilio, SendGrid, Resend, Brevo, Intercom

**DevOps & Cloud:**
- Vercel, Supabase, Sentry, Datadog, PagerDuty

**CRM & Marketing:**
- HubSpot, Shopify, Mailchimp, Airtable, Clerk

**CMS & Content:**
- Contentful, Sanity

**Search & Media:**
- Algolia, Cloudinary

**Analytics & Feature Flags:**
- PostHog, LaunchDarkly

**Automation:**
- n8n, Pipedream, Retool, Workato, Make

**Databases:**
- Upstash (Redis)

**Project Management:**
- ClickUp, Linear, Bitbucket

**Meetings:**
- Calendly, Zoom
- Raycast

---

### 📈 Stats

- **60+** Integrations
- **35+** AI Providers
- **100%** Python

---

## 🔧 Installation

```bash
pip install hellochusquis
```

## 📚 Documentation

- [README.md](../README.md) - Full documentation
- [docs/index.html](../docs/index.html) - Landing page
- [examples/README.md](../examples/README.md) - Usage examples

---

## 🤝 Thanks

- All contributors
- Community feedback