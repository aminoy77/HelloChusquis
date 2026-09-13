# Changelog

All notable changes to HelloChusquis. Older per-release notes previously lived in
`RELEASE_v*.md` files and are consolidated here.

## 5.4 — 2026-09-11

### Added
- Subagent system: main agent invokes unlimited specialists via one `subagent`
  tool (`list`/`run`/`fanout`/`custom`, incl. inline custom types). 12 builtins
  in `agents/<name>/AGENT.md`, isolated contexts, harness-enforced tool
  allowlists, hard budgets (12 steps / 12k tokens / 180s, 8 concurrent max),
  fanout outputs truncated to protect parent context.
- Subagent iteration 2: per-call `model`/`provider` routing, `isolated:true`
  writers in throwaway git worktrees (shell/code disabled, files
  path-contained, diff appended), harness-enforced flat hierarchy
  (subagents cannot spawn subagents).
- Telegram bridge: `hellochusquis telegram` chats from Telegram with
  allowlisted chat IDs, per-chat conversations, stdlib long-polling, no new deps.
- Subagent `chain` action: sequential pipelines where each step sees prior
  outputs (worker → reviewer); halts on first failure.
- Subagent `fail_fast` flag for fanout plus per-run `duration_s` timing and a
  fanout totals footer for observability.
- TUI: right info rail (session stats + live plan), centered command palette,
  multiline wrapping input with fixed dock layout (no more hidden rows).
- Landing (`docs/index.html`): unified numbers (120+ tools, 70+ providers),
  9→7 H2s, workflows replace testimonials, demo merged, fonts display=swap,
  no-JS fallback for the hero demo.

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

## 5.3 — 2026-09-11

### Fixed
- `hellochusquis web`: el botón Launch app no hacía nada porque el CSP con
  `nonce` bloquea los `onclick` inline; ahora usa `addEventListener`.
- `hellochusquis web`: ya no pide access key en local; el loopback
  (127.0.0.1/::1) entra como owner y el remoto sigue exigiendo Bearer.

### Changed
- Web app minimal en español con la misma paleta: sidebar con providers del
  usuario (badge listo + contador), Resumen Sesiones/Mensajes/Listos/Tools y
  welcome con stats de chats. Sin endpoints nuevos.

## Unreleased

### Added
- Subagent events (`run_start`/`tool_call`/`run_finish` callback plumbing for
  future streaming) and opt-in result cache: pure-reasoning outputs reused by
  TTL, tool runs always re-execute, 128-entry LRU ≈ 1 MB max.

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
