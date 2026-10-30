# OAuth Providers (Fase 1: Copilot + Qwen) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Browser-based OAuth login for GitHub Copilot and Qwen, storing tokens in the existing config and auto-refreshing them before API calls.

**Architecture:** New `core/oauth.py` holds a generic device-flow helper plus per-provider flows and a registry. `core/setup.py` offers "Login with browser" instead of the API-key prompt for OAuth providers. `core/provider.py` refreshes expired tokens before `_call` and adds Copilot-specific headers.

**Tech Stack:** Python 3, httpx (already a dependency), rich prompts (already used), pytest + monkeypatch (existing test style; no respx).

**Spec:** `docs/superpowers/specs/2026-10-24-oauth-providers-design.md`

## Global Constraints

- No new dependencies (httpx, rich, pyyaml already present).
- Tokens live in `~/.config/hellochusquis/config.yaml` (chmod 600 via existing `_save_config_securely`); never log or print full tokens.
- OAuth provider config entry shape (exact):
  `{"name": str, "base_url": str, "api_key": "<access_token>", "model": str, "priority": int, "oauth": {"provider": "copilot"|"qwen", "refresh": <secret used to refresh>, "expires_at": <unix float>}}`
- `core/provider.py` stays OpenAI-compatible only (Fase 2 adapters out of scope).
- Follow existing code style: rich `console`, `Prompt`/`Confirm` from rich.prompt, httpx.Client per call.

## Review Focus

- Device-flow poll timeout / user never authorizes → must stop after `expires_in` with a clear message, not hang forever. Test: `tests/test_oauth_device_flow.py::test_device_flow_times_out`.
- Poll endpoint returning `authorization_pending` then `slow_down` → must honor `interval` and `slow_down` (+5s) without crashing. Test: `tests/test_oauth_device_flow.py::test_device_flow_poll_states`.
- Copilot token expired mid-session → `_call` refreshes transparently, no user-visible failure. Test: `tests/test_provider_oauth_refresh.py::test_expired_token_refreshed_before_call`.
- Refresh secret missing/corrupt → clear error telling user to re-login, not a traceback. Test: `tests/test_provider_oauth_refresh.py::test_refresh_failure_message`.
- Token values must never appear in console output or logs. Test: `tests/test_oauth_device_flow.py::test_user_code_only_printed`.

---

### Task 1: Generic device-flow helper in `core/oauth.py`

**Files:**
- Create: `core/oauth.py`
- Test: `tests/test_oauth_device_flow.py`

**Interfaces:**
- Produces:
  - `device_flow(device_url: str, token_url: str, client_id: str, scope: str, open_browser: Callable[[str], None] = webbrowser.open, poll_interval: int = 5, timeout: float = 300.0, console) -> dict` — returns the token endpoint JSON dict (`access_token`, `refresh_token`, `expires_in`, ...). Raises `OAuthError` on timeout/denial.
  - `class OAuthError(Exception)` with user-facing `str` message.
  - `print_user_code(user_code: str, verification_uri: str, console)` — prints URI + code, opens browser.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_oauth_device_flow.py
import pytest
from core.oauth import device_flow, OAuthError, print_user_code

class FakeResp:
    def __init__(self, payload, status=200):
        self._payload, self.status_code = payload, status
    def json(self): return self._payload
    def raise_for_status(self):
        if self.status_code >= 400: raise RuntimeError(self.status_code)

def test_device_flow_success(monkeypatch):
    posts = []
    def fake_post(url, data=None, headers=None, timeout=None):
        posts.append((url, data))
        if len(posts) == 1:
            assert url.endswith("/device/code")
            return FakeResp({"device_code": "dc", "user_code": "ABCD-1234",
                             "verification_uri": "https://ex.ly", "interval": 1,
                             "expires_in": 60})
        assert data["grant_type"] == "urn:ietf:params:oauth:grant-type:device_code"
        return FakeResp({"access_token": "at", "refresh_token": "rt", "expires_in": 3600})
    monkeypatch.setattr("core.oauth.httpx.post", fake_post)
    opened = []
    tok = device_flow("https://ex.ly/device/code", "https://ex.ly/token",
                      "cid", "scope", open_browser=opened.append, poll_interval=0)
    assert tok["access_token"] == "at" and opened == ["https://ex.ly"]

def test_device_flow_poll_states(monkeypatch):
    responses = iter([
        FakeResp({"device_code": "dc", "user_code": "X", "verification_uri": "u",
                  "interval": 1, "expires_in": 60}),
        FakeResp({"error": "slow_down"}),
        FakeResp({"error": "authorization_pending"}),
        FakeResp({"access_token": "at"}),
    ])
    monkeypatch.setattr("core.oauth.httpx.post", lambda *a, **k: next(responses))
    tok = device_flow("u/d", "u/t", "cid", "s", open_browser=lambda u: None, poll_interval=0)
    assert tok["access_token"] == "at"

def test_device_flow_times_out(monkeypatch):
    monkeypatch.setattr("core.oauth.httpx.post", lambda *a, **k:
        FakeResp({"device_code": "dc", "user_code": "X", "verification_uri": "u",
                  "interval": 1, "expires_in": 1}))
    monkeypatch.setattr("core.oauth.time", None)  # replaced below
    import core.oauth as m
    monkeypatch.setattr(m.time, "time", lambda: 0)  # frozen clock; sleep patched too
    monkeypatch.setattr(m.time, "sleep", lambda s: None)
    with pytest.raises(OAuthError):
        device_flow("u/d", "u/t", "cid", "s", open_browser=lambda u: None, poll_interval=0)

def test_user_code_only_printed(capsys):
    print_user_code("SECRET-CODE", "https://ex.ly", console=None)  # console=None → fallback print
    out = capsys.readouterr().out
    assert "SECRET-CODE" in out and "access_token" not in out
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `python -m pytest tests/test_oauth_device_flow.py -v`
Expected: FAIL (`ModuleNotFoundError: core.oauth`)

- [ ] **Step 3: Implement `core/oauth.py`**

Module contents: `OAuthError`; `print_user_code` (rich console or fallback `print` — prints verification_uri and user_code only); `device_flow` implementing RFC 8628: POST device_url (`client_id`, `scope`) → print code + open browser → poll token_url with `grant_type=urn:ietf:params:oauth:grant-type:device_code`, `client_id`, `device_code`; handle `authorization_pending` (wait `interval`), `slow_down` (interval += 5), `access_denied`/`expired_token` (raise `OAuthError`), hard stop at `expires_in` (raise `OAuthError("Timed out waiting for authorization")`). Use `httpx.post(..., timeout=15)`.

- [ ] **Step 4: Run tests, verify pass**

Run: `python -m pytest tests/test_oauth_device_flow.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/oauth.py tests/test_oauth_device_flow.py
git commit -m "feat(oauth): generic RFC 8628 device-flow helper"
```

---

### Task 2: Copilot + Qwen flows and registry

**Files:**
- Modify: `core/oauth.py`
- Test: `tests/test_oauth_providers.py`

**Interfaces:**
- Consumes: `device_flow`, `OAuthError` (Task 1).
- Produces:
  - `OAUTH_PROVIDERS: dict[str, dict]` keyed by display name (`"GitHub Copilot"`, `"Qwen"`), each with keys: `oauth_provider` (`"copilot"`/`"qwen"`), `login() -> dict` returning `{access_token, refresh, expires_at, base_url, models}`.
  - `login_copilot() -> dict`, `login_qwen() -> dict`.
  - Copilot `refresh` field = the long-lived GitHub token (`gho_...`); `expires_at` = Copilot token expiry (unix).
  - Qwen `refresh` field = its `refresh_token`; `base_url` from token response `resource_url` + `/v1` (fallback `https://portal.qwen.ai/v1`); `models = ["qwen3-coder-plus", "qwen3-coder-flash"]`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_oauth_providers.py
import json
from core.oauth import login_copilot, login_qwen, OAUTH_PROVIDERS

class FakeResp:
    def __init__(self, payload): self._p = payload
    def json(self): return self._p
    def raise_for_status(self): pass

def test_registry_shape():
    assert set(OAUTH_PROVIDERS) == {"GitHub Copilot", "Qwen"}
    for name, info in OAUTH_PROVIDERS.items():
        assert info["oauth_provider"] in {"copilot", "qwen"}
        assert callable(info["login"])

def test_login_copilot(monkeypatch):
    calls = []
    def fake_post(url, data=None, headers=None, timeout=None):
        calls.append(url)
        if "device/code" in url:
            return FakeResp({"device_code": "dc", "user_code": "C", "verification_uri": "https://github.com/login/device", "interval": 1, "expires_in": 60})
        if "login/oauth/access_token" in url:
            return FakeResp({"access_token": "gho_x"})
        if "copilot_internal" in url:
            assert headers["Authorization"] == "token gho_x"
            return FakeResp({"token": "tid=1;exp=9999999999;sku=free", "expires_at": 9999999999})
    monkeypatch.setattr("core.oauth.httpx.post", fake_post)
    monkeypatch.setattr("core.oauth.httpx.get", lambda url, headers=None, timeout=None: FakeResp({}))
    monkeypatch.setattr("core.oauth.webbrowser.open", lambda u: None)
    tok = login_copilot(open_browser=lambda u: None)
    assert tok["access_token"] == "tid=1;exp=9999999999;sku=free"
    assert tok["refresh"] == "gho_x"
    assert tok["base_url"] == "https://api.githubcopilot.com"
    assert tok["expires_at"] == 9999999999

def test_login_qwen(monkeypatch):
    def fake_post(url, data=None, headers=None, timeout=None):
        if "device/code" in url:
            return FakeResp({"device_code": "dc", "user_code": "Q", "verification_uri": "https://chat.qwen.ai", "interval": 1, "expires_in": 60})
        return FakeResp({"access_token": "qat", "refresh_token": "qrt", "expires_in": 3600, "resource_url": "https://portal.qwen.ai"})
    monkeypatch.setattr("core.oauth.httpx.post", fake_post)
    tok = login_qwen(open_browser=lambda u: None)
    assert tok["access_token"] == "qat" and tok["refresh"] == "qrt"
    assert tok["base_url"] == "https://portal.qwen.ai/v1"
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `python -m pytest tests/test_oauth_providers.py -v`
Expected: FAIL (ImportError: `login_copilot`)

- [ ] **Step 3: Implement flows + registry in `core/oauth.py`**

- `login_copilot`: `device_flow("https://github.com/login/device/code", "https://github.com/login/oauth/access_token", client_id="Iv1.b507a08c87ecfe98", scope="read:user")` → GET `https://api.github.com/copilot_internal/v2/token` with `Authorization: token <gho>` and `User-Agent: HelloChusquis` → return dict per Interfaces. If exchange fails (non-200 / no `token`), raise `OAuthError("Copilot token exchange failed — is Copilot enabled on this account?")`.
- `login_qwen`: `device_flow("https://chat.qwen.ai/api/v1/oauth2/device/code", "https://chat.qwen.ai/api/v1/oauth2/token", client_id="f0304373b74a44d2b584a3fb70ca9f56", scope="openid profile email model.completion")` → dict per Interfaces.
- `OAUTH_PROVIDERS` maps display names to `{"oauth_provider": ..., "login": ...}`.
- Both accept `open_browser: Callable = None` param passed through to `device_flow` (defaults to `webbrowser.open`).

- [ ] **Step 4: Run tests, verify pass**

Run: `python -m pytest tests/test_oauth_providers.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/oauth.py tests/test_oauth_providers.py
git commit -m "feat(oauth): Copilot and Qwen login flows"
```

---

### Task 3: Setup integration — "Login with browser"

**Files:**
- Modify: `core/setup.py` (add-provider section, ~lines 620-650 and 870-895; also `pick_provider` list at ~line 137 for Copilot entry)
- Test: `tests/test_setup_oauth_login.py`

**Interfaces:**
- Consumes: `OAUTH_PROVIDERS`, `login()` (Task 2); `_save_config_securely(config)` (existing).
- Produces: `login_provider(config: dict, display_name: str) -> dict` — runs flow, appends/updates provider entry in `config["providers"]` with the Task-2 shape (`api_key=access_token`, `oauth={"provider", "refresh", "expires_at"}`), picks model via existing `pick_model(base_url, access_token, known_models=...)`, saves config, returns the entry.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_setup_oauth_login.py
from core import setup

def test_login_provider_builds_entry(monkeypatch):
    saved = {}
    monkeypatch.setattr(setup, "_save_config_securely", lambda c: saved.update(c) or "/tmp/x")
    monkeypatch.setattr(setup, "pick_model", lambda *a, **k: "gpt-4o")
    monkeypatch.setattr("core.oauth.OAUTH_PROVIDERS", {
        "GitHub Copilot": {"oauth_provider": "copilot", "login": lambda open_browser=None: {
            "access_token": "tok", "refresh": "gho", "expires_at": 123,
            "base_url": "https://api.githubcopilot.com", "models": ["gpt-4o"]}}})
    config = {"providers": []}
    entry = setup.login_provider(config, "GitHub Copilot")
    assert entry["api_key"] == "tok" and entry["oauth"]["provider"] == "copilot"
    assert entry["base_url"] == "https://api.githubcopilot.com"
    assert config["providers"] == [entry]
```

- [ ] **Step 2: Run test, verify it fails**

Run: `python -m pytest tests/test_setup_oauth_login.py -v`
Expected: FAIL (`AttributeError: login_provider`)

- [ ] **Step 3: Implement in `core/setup.py`**

- `login_provider(config, display_name)`: look up `OAUTH_PROVIDERS[display_name]`, call `info["login"]()` inside try/except `OAuthError` (print message, return None), build entry (shape above, `priority = len(existing)+1`, skip if a provider with same `oauth.provider` already exists → update it instead), append, save, print `✓ Logged in to {display_name}` (never print token), return entry.
- In the add-provider flow (`edit_config` new-provider section and the first-run `pick_provider` flow): if chosen provider name is in `OAUTH_PROVIDERS`, call `login_provider` instead of `_prompt_api_key` path.
- Add `"GitHub Copilot"` and `"Qwen"` entries to the `pick_provider` catalog (line ~137 area) with `"oauth": True` marker and their `base_url`/`models` from Task 2 constants (import from `core.oauth` to avoid duplication).

- [ ] **Step 4: Run test, verify pass**

Run: `python -m pytest tests/test_setup_oauth_login.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/setup.py tests/test_setup_oauth_login.py
git commit -m "feat(setup): browser login for OAuth providers"
```

---

### Task 4: Auto-refresh + Copilot headers in `core/provider.py`

**Files:**
- Modify: `core/provider.py` (`_call` at ~line 334, `Provider` class ~line 61)
- Test: `tests/test_provider_oauth_refresh.py`

**Interfaces:**
- Consumes: `OAUTH_PROVIDERS` / refresh logic from `core.oauth` (Task 2); provider config entries with `oauth` metadata (Task 3).
- Produces:
  - `Provider.oauth: dict | None` — loaded from config entry.
  - `refresh_oauth(provider: Provider) -> str` (module-level in `core/oauth.py`): returns fresh access token; for `copilot` re-exchanges via stored GitHub `refresh` token; for `qwen` uses `refresh_token` grant at its token endpoint; updates nothing itself (caller persists).
  - `ProviderPool._call`: before request, if `provider.oauth` and `time.time() >= provider.oauth["expires_at"] - 60` → call `refresh_oauth`, update `provider.api_key` and `provider.oauth["expires_at"]`, persist via existing config-save path used by `update_api_key`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_provider_oauth_refresh.py
import time as _time
from core import oauth
from core.provider import Provider

class FakeResp:
    def __init__(self, payload): self._p = payload
    def json(self): return self._p
    def raise_for_status(self): pass

def test_refresh_copilot(monkeypatch):
    monkeypatch.setattr(oauth.httpx, "get", lambda url, headers=None, timeout=None:
        FakeResp({"token": "newtok", "expires_at": 999}) if headers["Authorization"] == "token gho" else FakeResp({}))
    tok = oauth.refresh_oauth({"oauth": {"provider": "copilot", "refresh": "gho"}})
    assert tok["access_token"] == "newtok" and tok["expires_at"] == 999

def test_refresh_qwen(monkeypatch):
    monkeypatch.setattr(oauth.httpx, "post", lambda url, data=None, headers=None, timeout=None:
        FakeResp({"access_token": "q2", "refresh_token": "r2", "expires_in": 3600}))
    tok = oauth.refresh_oauth({"oauth": {"provider": "qwen", "refresh": "r1"}})
    assert tok["access_token"] == "q2" and tok["refresh"] == "r2"

def test_refresh_failure_message(monkeypatch):
    monkeypatch.setattr(oauth.httpx, "post", lambda *a, **k: FakeResp({"error": "bad"}))
    try:
        oauth.refresh_oauth({"oauth": {"provider": "qwen", "refresh": "bad"}})
        assert False, "should raise"
    except oauth.OAuthError as e:
        assert "re-login" in str(e).lower()

def test_expired_token_refreshed_before_call(monkeypatch):
    from core.provider import ProviderPool
    refreshed, sent = {}, {}
    monkeypatch.setattr(oauth, "refresh_oauth", lambda entry:
        refreshed.setdefault("called", True) or {"access_token": "fresh", "expires_at": 9999999999})
    pool = ProviderPool.__new__(ProviderPool)  # skip __init__; test _call only
    pool.timeout = 10
    pool.providers = []
    prov = Provider({"name": "copilot", "base_url": "https://api.githubcopilot.com",
                     "api_key": "old", "model": "gpt-4o",
                     "oauth": {"provider": "copilot", "refresh": "gho", "expires_at": 1}})
    def fake_post(self_url, headers=None, json=None, timeout=None):
        sent["auth"] = headers["Authorization"]
        return FakeResp({"choices": []})
    monkeypatch.setattr("core.provider.httpx.Client", lambda *a, **k: FakeClient(fake_post))
    pool._call(prov, [{"role": "user", "content": "hi"}], None)
    assert refreshed.get("called") and sent["auth"] == "Bearer fresh"
    assert prov.oauth["expires_at"] == 9999999999

class FakeClient:
    def __init__(self, post_fn, **kw): self._post = post_fn
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def post(self, url, headers=None, json=None, timeout=None):
        return self._post(url, headers=headers, json=json, timeout=timeout)
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `python -m pytest tests/test_provider_oauth_refresh.py -v`
Expected: FAIL (`AttributeError: refresh_oauth`)

- [ ] **Step 3: Implement**

- `core/oauth.py`: `refresh_oauth(entry: dict) -> dict` — dispatch on `entry["oauth"]["provider"]`; copilot: GET copilot_internal token endpoint with stored GitHub token; qwen: POST token endpoint with `grant_type=refresh_token`, `client_id`, `refresh_token`. Raise `OAuthError("...please re-login...")` on failure.
- `core/provider.py`: `Provider` gains `self.oauth = entry.get("oauth")` in `_load_config` path; in `_call`, before building headers: if `self.oauth` and expired (60s margin) → `fresh = refresh_oauth({"oauth": self.oauth})`, set `provider.api_key = fresh["access_token"]`, `provider.oauth["expires_at"] = fresh["expires_at"]`, persist through the same mechanism `update_api_key` uses; on `OAuthError` print the message once and re-raise as the existing error path. Copilot headers: when `api.githubcopilot.com` in base_url, add `Copilot-Integration-Id: hellochusquis` and `Editor-Version: hellochusquis/1.0`.

- [ ] **Step 4: Run tests, verify pass**

Run: `python -m pytest tests/test_provider_oauth_refresh.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/oauth.py core/provider.py tests/test_provider_oauth_refresh.py
git commit -m "feat(provider): transparent OAuth token refresh + Copilot headers"
```

---

### Task 5: CLI flag `--login` + end-to-end wiring

**Files:**
- Modify: `cli.py` (arg parsing near `--providers` at ~line 206)
- Test: `tests/test_cli_oauth_login.py`

**Interfaces:**
- Consumes: `login_provider` (Task 3).
- Produces: `hellochusquis --login "GitHub Copilot"` (also accepts `copilot`, `qwen` lowercase aliases) → runs browser login, saves config, exits 0. Unknown name → list valid names, exit 1.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cli_oauth_login.py
from core import setup

def test_alias_resolution():
    from core.oauth import OAUTH_PROVIDERS
    assert "GitHub Copilot" in OAUTH_PROVIDERS and "Qwen" in OAUTH_PROVIDERS

def test_cli_login_dispatch(monkeypatch, tmp_path):
    called = {}
    monkeypatch.setattr(setup, "login_provider", lambda cfg, name: called.setdefault("name", name))
    # dispatch function to be added in cli.py
    from cli import resolve_login_name
    assert resolve_login_name("copilot") == "GitHub Copilot"
    assert resolve_login_name("qwen") == "Qwen"
    assert resolve_login_name("nope") is None
```

- [ ] **Step 2: Run test, verify it fails**

Run: `python -m pytest tests/test_cli_oauth_login.py -v`
Expected: FAIL (`ImportError: resolve_login_name`)

- [ ] **Step 3: Implement in `cli.py`**

- `resolve_login_name(arg: str) -> str | None`: case-insensitive match against `OAUTH_PROVIDERS` keys and lowercase aliases (`copilot`, `ghc` → `"GitHub Copilot"`; `qwen` → `"Qwen"`).
- Add `--login NAME` argparse flag; handler: `config = ensure_config()`, `login_provider(config, name)`, exit 0; unknown → print valid names, exit 1.

- [ ] **Step 4: Run tests, verify pass**

Run: `python -m pytest tests/test_cli_oauth_login.py -v`
Expected: PASS

- [ ] **Step 5: Full suite + manual smoke**

Run: `python -m pytest tests/ -x -q`
Expected: all PASS

Manual: `python cli.py --login copilot` → browser opens to github.com/login/device, code shown; after auth, `✓ Logged in to GitHub Copilot` and config contains the entry with `oauth` metadata.

- [ ] **Step 6: Commit**

```bash
git add cli.py tests/test_cli_oauth_login.py
git commit -m "feat(cli): --login flag for OAuth providers"
```

---

### Task 6: Real SSE streaming in `core/provider.py`

**Files:**
- Modify: `core/provider.py` (after `_call`, ~line 375)
- Test: `tests/test_provider_streaming.py`

**Interfaces:**
- Consumes: existing `Provider`, `ProviderPool._available`, provider failover logic.
- Produces:
  - `ProviderPool.chat_stream(messages: List[dict], tools: Optional[List[dict]] = None, provider_name: str = None, model: str = None) -> Iterator[dict]` — yields `{"type": "reasoning", "content": str}` for `delta.reasoning_content`/`delta.reasoning`, `{"type": "chunk", "content": str}` for `delta.content`, `{"type": "tool_calls", "tool_calls": [accumulated dicts]}` when the model emits tool calls (stream ends there), `{"type": "error", "message": str}` on failure. Sends `"stream": true` in payload; parses SSE `data: {...}` lines, stops at `data: [DONE]`.
  - Tool-call delta accumulation: fragments keyed by `index`, concatenating `function.arguments`, collecting `id`/`name` on first sight.
  - Failover: if the request fails before the first yielded chunk, fall through to the next available provider (same order logic as `chat_with_retry`); after streaming started, emit `{"type": "error"}` instead of raising.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_provider_streaming.py
import json
import httpx
import pytest
from core.provider import ProviderPool

SSE_LINES = [
    'data: ' + json.dumps({"choices": [{"delta": {"reasoning_content": "think"}}]}),
    'data: ' + json.dumps({"choices": [{"delta": {"content": "Hel"}}]}),
    'data: ' + json.dumps({"choices": [{"delta": {"content": "lo"}}]}),
    'data: [DONE]',
]

class FakeStreamResp:
    status_code = 200
    def raise_for_status(self): pass
    def iter_lines(self): return iter(SSE_LINES)

def test_chat_stream_yields_reasoning_and_chunks(monkeypatch):
    pool = ProviderPool.__new__(ProviderPool)
    pool.providers = [Provider-like dict]  # use real Provider with test config
    captured = {}
    def fake_post(self, url, headers=None, json=None, timeout=None):
        captured["payload"] = json
        return FakeStreamResp()
    monkeypatch.setattr(httpx.Client, "post", fake_post)
    events = list(pool.chat_stream([{"role": "user", "content": "hi"}]))
    assert captured["payload"]["stream"] is True
    kinds = [(e["type"], e.get("content")) for e in events]
    assert ("reasoning", "think") in kinds
    assert ("chunk", "Hel") in kinds and ("chunk", "lo") in kinds

def test_chat_stream_accumulates_tool_calls(monkeypatch):
    # two fragments: index 0 name+args start, then args continuation
    ...yields {"type": "tool_calls", "tool_calls": [{"id": "c1", "function": {"name": "f", "arguments": '{"a":1}'}}]}

def test_chat_stream_failover_before_first_chunk(monkeypatch):
    # first provider raises httpx.ConnectError, second returns SSE → events come from second
```

(Implementer writes the two outlined tests fully against the Interfaces contract.)

- [ ] **Step 2: Run tests, verify they fail**

Run: `python -m pytest tests/test_provider_streaming.py -v`
Expected: FAIL (`AttributeError: chat_stream`)

- [ ] **Step 3: Implement `chat_stream` in `core/provider.py`**

Generator mirroring `_call`'s request setup (same headers/timeout logic) with `"stream": true`; `client.stream(...)` not required — `post(...)` with `iter_lines` on the response is enough for httpx. Accumulate tool-call fragments per Interfaces. On `httpx.HTTPStatusError`/connect error with zero chunks emitted → continue to next provider; after first chunk → yield error event.

- [ ] **Step 4: Run tests, verify pass**

Run: `python -m pytest tests/test_provider_streaming.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/provider.py tests/test_provider_streaming.py
git commit -m "feat(provider): real SSE streaming with reasoning + tool-call accumulation"
```

---

### Task 7: Real `agent.stream_run`

**Files:**
- Modify: `core/agent.py` (`stream_run`, lines ~1997-2075)
- Test: `tests/test_agent_stream_run.py`

**Interfaces:**
- Consumes: `ProviderPool.chat_stream` (Task 6); existing tool-execution block inside `stream_run`.
- Produces: `stream_run` yields `{"type": "reasoning", "content"}`, `{"type": "chunk", "content"}`, `{"type": "tool_call", ...}` (existing shape), `{"type": "done"}`. Final assistant content is added to history/session/memory exactly once (in the `done` path), same as today.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_agent_stream_run.py
def test_stream_run_yields_real_chunks(monkeypatch, minimal_agent):
    # minimal_agent: Agent built from test config with fake pool
    monkeypatch.setattr(ProviderPool, "chat_stream", lambda self, msgs, **k:
        iter([{"type": "reasoning", "content": "hmm"},
              {"type": "chunk", "content": "Hi"},
              {"type": "chunk", "content": " there"},
              {"type": "done"}]))
    events = list(minimal_agent.stream_run("hello"))
    kinds = [e["type"] for e in events]
    assert kinds == ["reasoning", "chunk", "chunk", "done"]
    assert minimal_agent.history.messages[-1]["content"] == "Hi there"
```

- [ ] **Step 2: Run test, verify it fails**

Run: `python -m pytest tests/test_agent_stream_run.py -v`
Expected: FAIL (current `stream_run` calls `chat_with_retry`, yields 50-char fake chunks)

- [ ] **Step 3: Implement**

Replace the `chat_with_retry` call in `stream_run` with `self.pool.chat_stream(...)`. Forward `reasoning`/`chunk` events as they arrive while accumulating full content; on `tool_calls` event run the existing tool loop (unchanged); on stream end without tool calls: `history.add` + `session_manager.append_message` + `memory.save_turn` (existing block), yield `{"type": "done"}`. Remove the 50-char fake chunking. Non-stream `run()` untouched (Telegram/API keep working).

- [ ] **Step 4: Run test, verify pass**

Run: `python -m pytest tests/test_agent_stream_run.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/agent.py tests/test_agent_stream_run.py
git commit -m "feat(agent): stream_run streams real provider SSE events"
```

---

### Task 8: TUI streaming UI — spinner, gray thinking box, live text

**Files:**
- Modify: `ui/tui.py` (`_run_message` ~line 700, `_set_processing` ~line 744, log helpers ~lines 478-590)
- Test: manual smoke (textual UI; no unit test — event mapping is thin)

**Interfaces:**
- Consumes: `agent.stream_run` events (Task 7).
- Produces: chat flow renders: `Spinner` while waiting for first event; `Collapsible(title="💭 Thinking", collapsed=True)` containing dim-gray `Static` updated live with reasoning; streaming answer text updated live in a `Static`; on `done` replaced by final `Markdown` via existing `_add_agent_md`.

- [ ] **Step 1: Implement**

- `_run_message`: replace `agent.run(text)` with iteration over `agent.stream_run(text)` via `call_from_thread` per event:
  - first event → hide spinner widget;
  - `reasoning` → ensure thinking `Collapsible` mounted, append dim text (`style="grey50"`) to its `Static`;
  - `chunk` → append to streaming `Static` (throttle updates to every ~100ms to keep TUI responsive);
  - `tool_call` → existing `_add_tool_call` rendering;
  - `done` → remove streaming `Static`, call existing `_add_agent_md(full_text)`.
- `_set_processing(True)` → mount/show `Spinner` widget in the log area; `(False)` → hide.
- Keep `_add_agent_md` as final renderer (Markdown, unchanged look).

- [ ] **Step 2: Manual smoke**

Run: `python cli.py` (chat REPL → TUI)
Check: spinner appears while waiting; thinking shows gray inside collapsible (expandable); answer streams in live; final message renders as Markdown; tool calls still render; input re-enables after done.

- [ ] **Step 3: Full suite**

Run: `python -m pytest tests/ -x -q`
Expected: all PASS

- [ ] **Step 4: Commit**

```bash
git add ui/tui.py
git commit -m "feat(tui): live streaming UI with spinner and collapsible thinking"
```
