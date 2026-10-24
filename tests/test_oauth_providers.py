"""Tests for Copilot and Qwen OAuth login flows."""
from core.oauth import login_copilot, login_qwen, OAUTH_PROVIDERS


class FakeResp:
    def __init__(self, payload):
        self._p = payload

    def json(self):
        return self._p

    def raise_for_status(self):
        pass


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
            return FakeResp({"device_code": "dc", "user_code": "C",
                             "verification_uri": "https://github.com/login/device",
                             "interval": 1, "expires_in": 60})
        if "login/oauth/access_token" in url:
            return FakeResp({"access_token": "gho_x"})
        raise AssertionError(f"unexpected POST {url}")

    def fake_get(url, headers=None, timeout=None):
        assert "copilot_internal" in url
        assert headers["Authorization"] == "token gho_x"
        return FakeResp({"token": "tid=1;exp=9999999999;sku=free",
                         "expires_at": 9999999999})

    monkeypatch.setattr("core.oauth.httpx.post", fake_post)
    monkeypatch.setattr("core.oauth.httpx.get", fake_get)
    tok = login_copilot(open_browser=lambda u: None)
    assert tok["access_token"] == "tid=1;exp=9999999999;sku=free"
    assert tok["refresh"] == "gho_x"
    assert tok["base_url"] == "https://api.githubcopilot.com"
    assert tok["expires_at"] == 9999999999
    assert tok["models"]


def test_login_copilot_exchange_failure(monkeypatch):
    def fake_post(url, data=None, headers=None, timeout=None):
        if "device/code" in url:
            return FakeResp({"device_code": "dc", "user_code": "C",
                             "verification_uri": "u", "interval": 1, "expires_in": 60})
        return FakeResp({"access_token": "gho_x"})

    monkeypatch.setattr("core.oauth.httpx.post", fake_post)
    monkeypatch.setattr("core.oauth.httpx.get",
                        lambda url, headers=None, timeout=None: FakeResp({}))
    from core.oauth import OAuthError
    try:
        login_copilot(open_browser=lambda u: None)
        assert False, "should raise"
    except OAuthError as e:
        assert "Copilot" in str(e)


def test_login_qwen(monkeypatch):
    def fake_post(url, data=None, headers=None, timeout=None):
        if "device/code" in url:
            return FakeResp({"device_code": "dc", "user_code": "Q",
                             "verification_uri": "https://chat.qwen.ai",
                             "interval": 1, "expires_in": 60})
        return FakeResp({"access_token": "qat", "refresh_token": "qrt",
                         "expires_in": 3600, "resource_url": "https://portal.qwen.ai"})

    monkeypatch.setattr("core.oauth.httpx.post", fake_post)
    tok = login_qwen(open_browser=lambda u: None)
    assert tok["access_token"] == "qat"
    assert tok["refresh"] == "qrt"
    assert tok["base_url"] == "https://portal.qwen.ai/v1"
    assert tok["models"]
