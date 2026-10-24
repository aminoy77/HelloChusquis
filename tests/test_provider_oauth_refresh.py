"""Tests for transparent OAuth refresh before provider calls."""
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


class FakeClient:
    def __init__(self, post_fn, **kw):
        self._post = post_fn

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def post(self, url, headers=None, json=None, timeout=None):
        return self._post(url, headers=headers, json=json, timeout=timeout)


def _pool_with(prov):
    pool = ProviderPool.__new__(ProviderPool)
    pool.timeout = 10
    pool.providers = [prov]
    return pool


def test_expired_token_refreshed_before_call(monkeypatch):
    refreshed, sent = {}, {}

    monkeypatch.setattr(oauth, "refresh_oauth", lambda entry:
        (refreshed.__setitem__("called", True),
         {"access_token": "fresh", "refresh": "gho", "expires_at": 9999999999})[1])
    prov = Provider(name="copilot", base_url="https://api.githubcopilot.com",
                    api_key="old", model="gpt-4o", priority=1,
                    oauth={"provider": "copilot", "refresh": "gho", "expires_at": 1})
    pool = _pool_with(prov)

    def fake_post(url, headers=None, json=None, timeout=None):
        sent["auth"] = headers.get("Authorization")
        return FakeResp({"choices": [{"message": {"content": "ok"}}]})

    monkeypatch.setattr("core.provider.httpx.Client", lambda *a, **k: FakeClient(fake_post))
    resp = pool._call(prov, [{"role": "user", "content": "hi"}], None)
    assert refreshed.get("called")
    assert sent["auth"] == "Bearer fresh"
    assert prov.api_key == "fresh"
    assert prov.oauth["expires_at"] == 9999999999
    assert resp["choices"][0]["message"]["content"] == "ok"


def test_valid_token_not_refreshed(monkeypatch):
    refreshed = {}

    def fail_refresh(entry):
        refreshed["called"] = True
        return {}

    monkeypatch.setattr(oauth, "refresh_oauth", fail_refresh)
    prov = Provider(name="copilot", base_url="https://api.githubcopilot.com",
                    api_key="tok", model="gpt-4o", priority=1,
                    oauth={"provider": "copilot", "refresh": "gho",
                           "expires_at": 9999999999})
    pool = _pool_with(prov)

    def fake_post(url, headers=None, json=None, timeout=None):
        return FakeResp({"choices": [{"message": {"content": "ok"}}]})

    monkeypatch.setattr("core.provider.httpx.Client", lambda *a, **k: FakeClient(fake_post))
    pool._call(prov, [{"role": "user", "content": "hi"}], None)
    assert not refreshed.get("called")


def test_copilot_headers_added(monkeypatch):
    sent = {}
    prov = Provider(name="copilot", base_url="https://api.githubcopilot.com",
                    api_key="tok", model="gpt-4o", priority=1)
    pool = _pool_with(prov)

    def fake_post(url, headers=None, json=None, timeout=None):
        sent.update(headers)
        return FakeResp({"choices": [{"message": {"content": "ok"}}]})

    monkeypatch.setattr("core.provider.httpx.Client", lambda *a, **k: FakeClient(fake_post))
    pool._call(prov, [{"role": "user", "content": "hi"}], None)
    assert sent["Copilot-Integration-Id"] == "hellochusquis"
    assert sent["Editor-Version"].startswith("hellochusquis/")
