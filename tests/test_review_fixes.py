"""Regression tests for the final-review fix pass."""
import httpx
import pytest

from core import oauth
from core.provider import Provider, ProviderPool


class FakeResp:
    def __init__(self, payload):
        self._p = payload

    def json(self):
        return self._p

    def raise_for_status(self):
        pass


# Fix 1: OAuthError in non-stream chat() must fail over, not traceback.
def test_chat_failover_on_oauth_error(monkeypatch):
    p1 = Provider(name="p1", base_url="https://a.example.com/v1", api_key="k",
                  model="m", priority=1,
                  oauth={"provider": "copilot", "refresh": "gho", "expires_at": 1})
    p2 = Provider(name="p2", base_url="https://b.example.com/v1", api_key="k",
                  model="m", priority=2)
    pool = ProviderPool.__new__(ProviderPool)
    pool.timeout = 10
    pool.providers = [p1, p2]

    def fake_call(self, provider, messages, tools, model=None):
        if provider.name == "p1":
            raise oauth.OAuthError("Copilot token refresh failed — please re-login.")
        return {"choices": [{"message": {"content": "ok"}}]}

    monkeypatch.setattr(ProviderPool, "_call", fake_call)
    resp = pool.chat([{"role": "user", "content": "hi"}])
    assert resp["choices"][0]["message"]["content"] == "ok"


def test_refresh_network_error_wrapped(monkeypatch):
    monkeypatch.setattr(oauth.httpx, "get",
                        lambda *a, **k: (_ for _ in ()).throw(httpx.ConnectError("down")))
    with pytest.raises(oauth.OAuthError):
        oauth.refresh_oauth({"oauth": {"provider": "copilot", "refresh": "gho"}})


# Fix 2: mid-stream error with partial content must surface, not save silently.
def test_stream_run_partial_then_error(monkeypatch):
    from types import SimpleNamespace
    from core.agent import Agent

    agent = Agent.__new__(Agent)
    agent.pool = SimpleNamespace(chat_stream=lambda *a, **k: iter([
        {"type": "chunk", "content": "par"},
        {"type": "error", "message": "mid-stream drop"},
    ]))
    agent.history = SimpleNamespace(add=lambda *a: None, messages=[],
                                    get_token_count=lambda m: 0,
                                    optimize_context=lambda max_tokens=0: [])
    agent.session_manager = SimpleNamespace(append_message=lambda *a: None)
    agent._session_id = "t"
    agent._pending_tool_results = []
    agent.tools_schema = None
    agent._build_messages = lambda: [{"role": "user", "content": "hi"}]

    import core.agent as agent_mod
    monkeypatch.setattr(agent_mod, "memory", SimpleNamespace(
        save_turn=lambda *a, **k: None, recall_context=lambda *a, **k: None))

    events = list(agent.stream_run("hi"))
    kinds = [e["type"] for e in events]
    assert "error" in kinds
    assert kinds[-1] == "done"


# Fix 4: network errors during login become OAuthError, not tracebacks.
def test_device_flow_network_error(monkeypatch):
    monkeypatch.setattr(oauth.httpx, "post",
                        lambda *a, **k: (_ for _ in ()).throw(httpx.ConnectError("offline")))
    with pytest.raises(oauth.OAuthError):
        oauth.device_flow("u/d", "u/t", "cid", "s", open_browser=lambda u: None)


def test_login_copilot_exchange_network_error(monkeypatch):
    def fake_post(url, data=None, headers=None, timeout=None):
        if "device/code" in url:
            return FakeResp({"device_code": "dc", "user_code": "C",
                             "verification_uri": "u", "interval": 1, "expires_in": 60})
        return FakeResp({"access_token": "gho_x"})

    monkeypatch.setattr(oauth.httpx, "post", fake_post)
    monkeypatch.setattr(oauth.httpx, "get",
                        lambda *a, **k: (_ for _ in ()).throw(httpx.ConnectError("down")))
    with pytest.raises(oauth.OAuthError):
        oauth.login_copilot(open_browser=lambda u: None)


# Fix 3: editing a provider must not wipe its oauth metadata.
def test_edit_config_preserves_oauth(monkeypatch):
    from core import setup

    config = {"providers": [{
        "name": "GitHub Copilot-1", "base_url": "https://api.githubcopilot.com",
        "api_key": "oldtok", "model": "gpt-4o", "priority": 1,
        "oauth": {"provider": "copilot", "refresh": "gho", "expires_at": 1}}]}
    monkeypatch.setattr(setup, "ensure_config", lambda: config)
    monkeypatch.setattr(setup, "_save_config_securely", lambda c: "/tmp/x")
    monkeypatch.setattr(setup, "_check_providers_valid", lambda c: None)
    answers = iter(["", "", "", ""])  # name, base_url, api_key, model → keep defaults
    monkeypatch.setattr(setup.Prompt, "ask", lambda *a, **k: next(answers))
    monkeypatch.setattr(setup.Confirm, "ask", lambda *a, **k: False)

    setup.edit_config("providers")
    p = config["providers"][0]
    assert p.get("oauth") == {"provider": "copilot", "refresh": "gho", "expires_at": 1}
