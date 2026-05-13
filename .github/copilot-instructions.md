## HelloChusquis — Copilot instructions (concise)

Purpose: help AI coding agents be immediately productive in this repo by highlighting the big picture, developer workflows, project conventions, and concrete examples.

- Big picture
  - Core components live under `core/`: `agent.py` (main runtime), `builder.py` (plugin builder), `plugin_loader.py` (dynamic plugins), `runner.py` (background tasks), `planner.py` (plan generation).
  - `tools/` contains many integration wrappers (github, slack, docker, files, shell, code, websearch). Agents call tools via a function-style schema constructed in `core.agent._build_tools_schema()`.
  - CLI entry is `cli.py` (script `hellochusquis` in `pyproject.toml`). Main interactive loop is in `main.py`. Web UI under `web/` and API under `api/main.py`.

- How requests flow (use this mental model)
  - CLI (`hellochusquis` / `main.py`) or API (`api/main.py`) -> `Agent` (`core/agent.py`) -> `Planner` (for complex tasks) -> ProviderPool (LLMs) + Tool calls (from `tools/`) -> plugin hooks (from `core/plugin_loader.py`).

- Key developer workflows
  - Local quick run (fast smoke):
    - `python cli.py` or `hellochusquis` (after installing). This launches the terminal UI (`main.py`).
    - Start web UI: `hellochusquis web` or run `uvicorn api.main:app --reload --port 8000` then open http://localhost:8000.
    - Start REST API: `hellochusquis api --port 8080` (CLI wraps `api.main`).
  - Plugin development: `core/builder.py` contains the plugin-builder flow. Plugins live in `~/.hellochusquis/plugins` (default) and must expose `PLUGIN_NAME`, `PLUGIN_SCHEMA` and a `run(...) -> str` API (see builder prompt template).

- Project-specific conventions
  - Config: `config.yaml` at repo root (and `~/.hellochusquis/config.yaml` for runtime) drives providers, priorities, timeouts, and the system prompt. Prefer absolute paths (the system prompt enforces this).
  - Plugins: always return strings from `run()`; handle exceptions and return human-friendly error strings instead of propagating raw exceptions.
  - Tools are declared as function schemas (see `_build_tools_schema` in `core/agent.py`); use those canonical tool names: `shell`, `code`, `web_search`, plus service-specific names like `github`, `slack`, `docker`.

- Small concrete examples (copy/paste friendly)
  - Call the web UI from the repo: `hellochusquis web` (calls `web.server` via `cli.py`).
  - Start API using uvicorn directly: `uvicorn api.main:app --reload --port 8080`.
  - Create a plugin template: use `core/plugin_loader.PluginLoader.create_plugin_template(name)` or follow the template in `core/builder.py` (must set `PLUGIN_NAME`, `PLUGIN_SCHEMA`, `run`).

- Errors & edge cases
  - If providers are exhausted, `main.py` prints provider guidance and points to `~/.hellochusquis/config.yaml` for keys; prefer reproducing those exact messages when suggesting fixes.
  - Background tasks use `core/runner.py`; check `get_runner()` and registered tasks for status/logs.

- What to avoid / follow strictly
  - Do not invent runtime paths/apis. Use `config.yaml`, `core/*`, `tools/*` and `api/main.py` as ground truth.
  - Follow the plugin contract exactly. Tests and the builder expect `PLUGIN_NAME`, `PLUGIN_SCHEMA`, `run()` to exist.

- Where to look first when editing or debugging
  - `core/agent.py` — runtime orchestration, tool schemas, provider pool usage.
  - `main.py` & `cli.py` — entry points and common flags (`--quick`, `--full`, `--show`, `web`, `api`).
  - `core/builder.py` & `core/plugin_loader.py` — plugin generation, testing and discovery.
  - `config.yaml` — provider setup, timeouts, and system prompt with agent rules.

If anything here is unclear or you want more detail (examples for a specific file, plugin template, or common edit task), say which area and I'll iterate.
