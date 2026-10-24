"""Tests for the generic RFC 8628 device-flow helper in core/oauth.py."""
import pytest

from core.oauth import device_flow, OAuthError, print_user_code


class FakeResp:
    def __init__(self, payload, status=200):
        self._payload, self.status_code = payload, status

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)


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
        assert data["device_code"] == "dc"
        return FakeResp({"access_token": "at", "refresh_token": "rt", "expires_in": 3600})

    monkeypatch.setattr("core.oauth.httpx.post", fake_post)
    opened = []
    tok = device_flow("https://ex.ly/device/code", "https://ex.ly/token",
                      "cid", "scope", open_browser=opened.append, poll_interval=0)
    assert tok["access_token"] == "at"
    assert tok["refresh_token"] == "rt"
    assert opened == ["https://ex.ly"]


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
    import core.oauth as m
    monkeypatch.setattr("core.oauth.httpx.post", lambda *a, **k:
        FakeResp({"device_code": "dc", "user_code": "X", "verification_uri": "u",
                  "interval": 1, "expires_in": 1}))
    clock = {"now": 0.0}
    monkeypatch.setattr(m.time, "time", lambda: clock["now"])
    monkeypatch.setattr(m.time, "sleep", lambda s: clock.__setitem__("now", clock["now"] + s))
    with pytest.raises(OAuthError):
        device_flow("u/d", "u/t", "cid", "s", open_browser=lambda u: None, poll_interval=0)


def test_device_flow_access_denied(monkeypatch):
    responses = iter([
        FakeResp({"device_code": "dc", "user_code": "X", "verification_uri": "u",
                  "interval": 1, "expires_in": 60}),
        FakeResp({"error": "access_denied"}),
    ])
    monkeypatch.setattr("core.oauth.httpx.post", lambda *a, **k: next(responses))
    with pytest.raises(OAuthError):
        device_flow("u/d", "u/t", "cid", "s", open_browser=lambda u: None, poll_interval=0)


def test_user_code_only_printed(capsys):
    print_user_code("SECRET-CODE", "https://ex.ly", console=None)
    out = capsys.readouterr().out
    assert "SECRET-CODE" in out
    assert "access_token" not in out
