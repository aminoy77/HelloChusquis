# Release v5.0

**Date:** August 5, 2026

## Highlights

Major release expanding the provider catalog from 35 to 54 AI providers, adding 20+ new tool integrations, enabling SSE streaming across all endpoints, and hardening security against advanced shell attack patterns.

## What's New

### 54-Provider Catalog
- Expanded from 35 to 54 AI providers across 9 categories
- **New providers:** Cerebras, NVIDIA NIM, DeepInfra, SiliconFlow, Volcengine, Baidu Qianfan, Tencent Hunyuan, StepFun, Jina AI, FriendliAI, LM Studio, vLLM, Jan, AI21, TextCortex, Baseten, Modal, TextGen WebUI, LocalAI, AnythingLLM
- Every provider now includes a `models` field with known model IDs
- `fetch_available_models`: live `/models` endpoint + known catalog merge (no duplicates)
- `pick_provider`: shows ALL 54 providers grouped by 9 categories
- `pick_model`: paginated list, number or text search, known fallback

### Unified Setup Flow
- `run_quick_setup`: pick any provider from full catalog, enter key (or skip for local), pick from ALL models, save config
- `run_setup` / `edit_config`: use new `pick_provider` / `pick_model` with model lists
- `provider.py list_models`: pass `provider_name` to `fetch_available_models`

### SSE Streaming
- `/clear` and `/status` now return Server-Sent Events (StreamingResponse) with chunk/done events
- `/chat/stream` endpoint for real-time streaming responses
- Web UI: async chat → sync (threadpool) — event loop no longer stalls

### 20+ New Tool Integrations
GitHub, Discord, Stripe, Shopify, Notion, Twilio, HubSpot, Intercom, Mailchimp, MongoDB, PagerDuty, Datadog, ClickUp, Resend, Sanity, Vercel, Clerk, Google Calendar, Docker, Brevo

### Security Hardening Round 2
- Block long-form rm (`--recursive --force`, all GNU/macOS variants)
- Block renamed fork bombs (`f(){ f|f& };f` pattern)
- Block `halt`/`poweroff`/`systemctl poweroff`/`osascript shutdown`
- Block `kill -SIGKILL`/`-KILL`/`-TERM` on init/group/all
- Block 2-stage RCE (`curl -o && sh`, `bash <(curl)`, `curl|xargs sh`)
- Block `python -c` with `os`/`shutil`/`subprocess`/`pathlib` imports
- Block `mke2fs`/`newfs_hfs`/`diskutil erase`
- Block `find -delete` on `/`/`home`/`~`, `chmod -R a+rwx /`

### Performance
- `db_memory`: flat write path (vocab cache, incremental fit, no per-write scan)
- `db_memory`: no per-query `build_vocabulary` (reuses cached vocab index)
- `db_memory`: str path coercion in `_connect`
- `db_memory`: `auto_embed` crash fix (4-col unpack)

### UI
- New TUI interface (`ui/tui.py` — 481 lines)
- Web UI restructured sidebar (Providers, Memory, Learnings panels)
- Model dropdown population fix in web UI
- Auth opt-in via `HELLOCHUSQUIS_AUTH` env (default: disabled for local use)
- `OPTIONS` passthrough (CORS preflight)

### Cleanup
- Deleted obsolete `refactor_agent.py` script
- Removed community attribution from README

## Files Changed

```
README.md                  |   2 +-
core/agent.py              |  18 +++
core/db_memory.py          | 204 ++++++++++++-
core/provider.py           |  58 +++++-
core/security_evaluator.py | 119 ++++++++++-
core/setup.py              | 468 +++++++++++++++++++++++++++++
docs/index.html            | 316 +++++++++++++++++++++++++
main.py                    | 117 +-----------
pyproject.toml             |   4 +-
tools/brevo.py             |  64 +++
tools/clerk.py             |  64 +++
tools/clickup.py           |  68 +++
tools/datadog.py           |  67 +++
tools/discord.py           |  67 +++
tools/github.py            | 136 +++++++
tools/google_calendar.py   |  67 +++
tools/hubspot.py           |  62 +++
tools/intercom.py          |  66 +++
tools/mailchimp.py         |  67 +++
tools/mongodb.py           |  65 +++
tools/notion.py            |  69 +++
tools/pagerduty.py         |  80 +++
tools/resend.py            |  62 +++
tools/sanity.py            |  67 +++
tools/shopify.py           |  63 +++
tools/stripe.py            |  60 +++
tools/vercel.py            |  64 +++
tools/websearch.py         | 268 +++++++++++++
tools/zoom.py              |  62 +++
ui/terminal.py             | 116 +++++++
ui/tui.py                  | 481 ++++++++++++++++++++++++++
web/index.html             | 4096 +++++++++++++++++++++++++
web/server.py              | 107 +++++++
workspace/manager.py       |  22 ++
```

## Breaking Changes

None. All existing configurations and API keys continue to work.

## Upgrade

```bash
pip install --upgrade hellochusquis
```

## Links

- [GitHub](https://github.com/aminoy77/HelloChusquis)
- [PyPI](https://pypi.org/project/hellochusquis)
- [Documentation](https://aminoy77.github.io/HelloChusquis/)
