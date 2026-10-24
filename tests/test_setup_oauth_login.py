"""Tests for browser-login integration in core/setup.py."""
from core import setup


def test_login_provider_builds_entry(monkeypatch):
    saved = {}
    monkeypatch.setattr(setup, "_save_config_securely",
                        lambda c: saved.update(c) or "/tmp/x")
    monkeypatch.setattr(setup, "pick_model", lambda *a, **k: "gpt-4o")
    monkeypatch.setattr("core.oauth.OAUTH_PROVIDERS", {
        "GitHub Copilot": {"oauth_provider": "copilot",
                           "login": lambda open_browser=None: {
                               "access_token": "tok", "refresh": "gho",
                               "expires_at": 123,
                               "base_url": "https://api.githubcopilot.com",
                               "models": ["gpt-4o"]}}})
    config = {"providers": []}
    entry = setup.login_provider(config, "GitHub Copilot")
    assert entry["api_key"] == "tok"
    assert entry["oauth"]["provider"] == "copilot"
    assert entry["oauth"]["refresh"] == "gho"
    assert entry["oauth"]["expires_at"] == 123
    assert entry["base_url"] == "https://api.githubcopilot.com"
    assert entry["model"] == "gpt-4o"
    assert config["providers"] == [entry]
    assert saved.get("providers") == [entry]


def test_login_provider_updates_existing(monkeypatch):
    monkeypatch.setattr(setup, "_save_config_securely", lambda c: "/tmp/x")
    monkeypatch.setattr(setup, "pick_model", lambda *a, **k: "gpt-4o")
    monkeypatch.setattr("core.oauth.OAUTH_PROVIDERS", {
        "GitHub Copilot": {"oauth_provider": "copilot",
                           "login": lambda open_browser=None: {
                               "access_token": "tok2", "refresh": "gho2",
                               "expires_at": 456,
                               "base_url": "https://api.githubcopilot.com",
                               "models": ["gpt-4o"]}}})
    config = {"providers": [{"name": "GitHub Copilot-1",
                             "base_url": "https://api.githubcopilot.com",
                             "api_key": "old", "model": "gpt-4o", "priority": 1,
                             "oauth": {"provider": "copilot", "refresh": "old",
                                       "expires_at": 1}}]}
    entry = setup.login_provider(config, "GitHub Copilot")
    assert len(config["providers"]) == 1
    assert entry["api_key"] == "tok2"
    assert entry["oauth"]["refresh"] == "gho2"


def test_login_provider_oauth_error_returns_none(monkeypatch):
    from core.oauth import OAuthError
    monkeypatch.setattr("core.oauth.OAUTH_PROVIDERS", {
        "Qwen": {"oauth_provider": "qwen",
                 "login": lambda open_browser=None: (_ for _ in ()).throw(
                     OAuthError("Timed out"))}})
    config = {"providers": []}
    assert setup.login_provider(config, "Qwen") is None
    assert config["providers"] == []
