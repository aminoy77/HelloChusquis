# Changelog

All notable changes to HelloChusquis. Older per-release notes previously lived in
`RELEASE_v*.md` files and are consolidated here.

## Unreleased

### Fixed
- `secret_scanner` raised `UnboundLocalError` on every action because `os` was re-imported
  inside `run()`, shadowing the module-level import.
- The `AWS_SECRET` detection pattern used a mid-pattern `(?-i)` scoped flag, which Python's `re`
  rejects; every `secret_scanner` scan raised on it (silently swallowed during file scans).
- Installing the package no longer leaves the default TUI unusable: `textual` is a declared
  dependency instead of an implicit one.
- `tools/aws_s3`, `tools/cloudflare_r2`, `tools/do_spaces`, `tools/wasabi` and `tools/voice`
  no longer import their SDK at module load, so they can be imported (and tested) without
  optional dependencies installed. Calling them without the SDK returns an actionable
  "install `hellochusquis[aws]`" style error.

### Added
- Multi-user identity: named principals with `viewer`/`operator`/`owner` roles, tokens stored
  only as hashes in `~/.hellochusquis/identity.db`, revocation, and `hellochusquis users
  add|list|revoke`. The deployment-wide `HELLOCHUSQUIS_API_KEY` keeps working as an owner token.
- Owner-only `/users` endpoints on the REST API, and role checks on every authenticated
  API and web route.
- Authorization at tool dispatch: a viewer cannot reach a mutating tool even via the model, and
  approved actions are re-checked against the caller's current role before execution.
- HTTP conversation sessions are scoped to their principal, so the same session header from two
  users no longer shares agent state.
- Optional install extras: `aws`, `voice`, `watch`, `dev`.
- GitHub Actions CI: ruff lint, unit tests on Python 3.10/3.11/3.12, an import smoke check of
  every bundled module, and the offline `doctor --contracts` diagnostic.
- Ruff configuration in `pyproject.toml`.

### Removed
- `core/watchdog.py`, which was marked deprecated, unused, and pulled in an undeclared dependency.
- Committed build artifacts under `dist/` (stale 1.4.2 wheel and sdist).

## 5.0 — 2026-08-05

Major release expanding the provider catalog from 35 to 54 AI providers, adding 20+ tool
integrations, enabling SSE streaming across endpoints, and hardening shell security.

- **54-provider catalog** across 9 categories, each provider carrying a `models` list;
  `fetch_available_models` merges the live `/models` endpoint with the known catalog.
- **Unified setup flow** — `run_quick_setup`, `run_setup` and `edit_config` share the same
  provider/model pickers with pagination and search.
- **SSE streaming** — `/clear` and `/status` return Server-Sent Events; `/chat/stream` streams
  responses in real time.
- **20+ new integrations** — GitHub, Discord, Stripe, Shopify, Notion, Twilio, HubSpot, Intercom,
  Mailchimp, MongoDB, PagerDuty, Datadog, ClickUp, Resend, Sanity, Vercel, Clerk, Google Calendar,
  Docker, Brevo.
- **Security hardening round 2** — blocks long-form `rm`, renamed fork bombs, halt/poweroff,
  signal kills on init, 2-stage RCE (`curl -o && sh`, `bash <(curl)`), `python -c` with dangerous
  imports, filesystem destruction and recursive `chmod`/`find -delete` on system roots.
- **Performance** — `db_memory` flat write path, cached vocabulary, no per-query rebuild.
- **UI** — new `ui/tui.py`, restructured web sidebar (Providers, Memory, Learnings).

No breaking changes.

## 1.4.2

- Expanded quick setup from 3 to 15 AI providers, each with base URL and default model.
- Removed old release notes and build artifacts.

## 1.4.1

- Fixed a `MarkupError` in quick setup (`[bold>` → `[bold]`).

## 1.4.0

- OpenRouter 402 errors now suggest provider alternatives.
- URL protocol validation adds `https://` when missing.
- Quick setup offers OpenRouter, Groq or Ollama.
- Web-search awareness in the system prompt (DuckDuckGo).
- `BackgroundRunner` gained exponential backoff and logging.

## 1.3.1

- `--api-keys` correctly updates API keys.
- All config flags work: `--show`, `--api-keys`, `--providers`, `--quick`, `--full`.
