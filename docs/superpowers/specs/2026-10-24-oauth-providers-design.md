# OAuth Providers — Design

## Intent
Login to LLM providers via browser OAuth instead of pasting API keys. User runs
`hellochusquis --providers` (or a new `--login <provider>`), browser opens, user
logs in once, token is stored and auto-refreshed afterwards.

## Goals
- Browser-based login for: GitHub Copilot, Qwen (Fase 1); Claude Code, Gemini CLI, Codex (Fase 2).
- Tokens stored in existing config (`~/.config/hellochusquis/config.yaml`, chmod 600) as `api_key`, plus refresh metadata.
- Auto-refresh: expired token refreshed transparently before a call fails.
- Zero manual key pasting for OAuth providers.

## Non-goals
- OAuth for tools (Gmail/Spotify) — separate concern.
- Multi-account per provider.
- New CLI framework — reuse existing `edit_config` / `ProviderPool`.

## Constraints
- `core/provider.py` only speaks OpenAI-compatible `/chat/completions`.
  - Fase 1 providers fit: Copilot (`api.githubcopilot.com`, needs extra headers
    `Copilot-Integration-Id`/`Editor-Version` + 30-min token auto-refresh), Qwen
    (OpenAI-compat endpoint).
  - Fase 2 providers (Claude = Anthropic Messages, Gemini = Code Assist
    `generateContent`, Codex = ChatGPT Responses API) need request/response
    adapters in `provider.py`. Deferred to Fase 2.

## Approaches considered
1. **Phased (chosen)** — Fase 1: OAuth infra + Copilot + Qwen. Fase 2: adapters
   for Claude/Gemini/Codex. Smallest working slice first.
2. All five at once — 3-4x scope, delays first working login.
3. Only Fase 1, drop the rest — leaves 3 providers unusable.

## Design (Fase 1)
- New module `core/oauth.py`:
  - `flows/` per provider: `copilot` (GitHub device flow: device code →
    github.com/login/device → poll access token → exchange for Copilot token),
    `qwen` (device flow at chat.qwen.ai).
  - Common helpers: open browser (`webbrowser`), poll token endpoint, store
    `{access_token, refresh_token, expires_at, type}` under
    `provider["oauth"]` in config.
- `core/setup.py`: new `login_provider(name)` action; in the add-provider flow,
  OAuth providers offer "Login with browser" instead of `_prompt_api_key`.
- `core/provider.py`: before `_call`, if provider has `oauth` metadata and token
  expired → refresh (Copilot: re-exchange GitHub token; Qwen: refresh_token
  grant). Copilot extra headers added in `_call` when base_url is Copilot.
- Config shape per OAuth provider:
  `{"name": ..., "base_url": ..., "model": ..., "api_key": "<access_token>",
    "oauth": {"provider": "copilot", "refresh_token": ..., "expires_at": ...}}`

## Left to the builder
- Exact client_ids / endpoints per flow (well-known public values of each CLI).
- Poll interval / timeout UX for device flow.
- Whether refresh happens lazily in `_call` or via a pre-flight check.
