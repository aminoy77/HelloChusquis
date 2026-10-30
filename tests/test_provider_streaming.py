"""Tests for real SSE streaming in ProviderPool.chat_stream."""
import json

import httpx
import pytest

from core.provider import Provider, ProviderPool


def sse(*deltas):
    lines = ['data: ' + json.dumps({"choices": [{"delta": d}]}) for d in deltas]
    lines.append("data: [DONE]")
    return lines


class FakeStreamResp:
    status_code = 200

    def __init__(self, lines):
        self._lines = lines

    def raise_for_status(self):
        pass

    def iter_lines(self):
        return iter(self._lines)


class FakeClient:
    def __init__(self, post_fn, **kw):
        self._post = post_fn

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def post(self, url, headers=None, json=None, timeout=None):
        return self._post(url, headers=headers, json=json, timeout=timeout)

    class _StreamCtx:
        def __init__(self, resp):
            self._resp = resp

        def __enter__(self):
            return self._resp

        def __exit__(self, *a):
            return False

    def stream(self, method, url, headers=None, json=None, timeout=None):
        return self._StreamCtx(self._post(url, headers=headers, json=json, timeout=timeout))


def _pool(*providers):
    pool = ProviderPool.__new__(ProviderPool)
    pool.timeout = 10
    pool.providers = list(providers)
    return pool


def test_chat_stream_yields_reasoning_and_chunks(monkeypatch):
    captured = {}
    prov = Provider(name="p1", base_url="https://api.example.com/v1",
                    api_key="k", model="m", priority=1)
    pool = _pool(prov)

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["payload"] = json
        return FakeStreamResp(sse({"reasoning_content": "think"},
                                  {"content": "Hel"}, {"content": "lo"}))

    monkeypatch.setattr("core.provider.httpx.Client", lambda *a, **k: FakeClient(fake_post))
    events = list(pool.chat_stream([{"role": "user", "content": "hi"}]))
    assert captured["payload"]["stream"] is True
    kinds = [(e["type"], e.get("content")) for e in events]
    assert ("reasoning", "think") in kinds
    assert ("chunk", "Hel") in kinds
    assert ("chunk", "lo") in kinds


def test_chat_stream_accumulates_tool_calls(monkeypatch):
    prov = Provider(name="p1", base_url="https://api.example.com/v1",
                    api_key="k", model="m", priority=1)
    pool = _pool(prov)
    lines = [
        'data: ' + json.dumps({"choices": [{"delta": {"tool_calls": [
            {"index": 0, "id": "c1", "function": {"name": "f", "arguments": '{"a"'}}]}}]}),
        'data: ' + json.dumps({"choices": [{"delta": {"tool_calls": [
            {"index": 0, "function": {"arguments": ':1}'}}]}}]}),
        "data: [DONE]",
    ]

    monkeypatch.setattr("core.provider.httpx.Client",
                        lambda *a, **k: FakeClient(lambda *a2, **k2: FakeStreamResp(lines)))
    events = list(pool.chat_stream([{"role": "user", "content": "hi"}]))
    tc = [e for e in events if e["type"] == "tool_calls"]
    assert len(tc) == 1
    assert tc[0]["tool_calls"] == [{"id": "c1", "function": {"name": "f", "arguments": '{"a":1}'}}]


def test_chat_stream_failover_before_first_chunk(monkeypatch):
    p1 = Provider(name="p1", base_url="https://down.example.com/v1",
                  api_key="k", model="m", priority=1)
    p2 = Provider(name="p2", base_url="https://up.example.com/v1",
                  api_key="k", model="m", priority=2)
    pool = _pool(p1, p2)
    state = {"n": 0}

    def fake_post(url, headers=None, json=None, timeout=None):
        state["n"] += 1
        if state["n"] == 1:
            raise httpx.ConnectError("boom")
        return FakeStreamResp(sse({"content": "ok"}))

    monkeypatch.setattr("core.provider.httpx.Client", lambda *a, **k: FakeClient(fake_post))
    events = list(pool.chat_stream([{"role": "user", "content": "hi"}]))
    assert state["n"] == 2
    assert ("chunk", "ok") in [(e["type"], e.get("content")) for e in events]


def test_chat_stream_error_after_first_chunk(monkeypatch):
    prov = Provider(name="p1", base_url="https://api.example.com/v1",
                    api_key="k", model="m", priority=1)
    pool = _pool(prov)

    class MidFailResp:
        status_code = 200
        def raise_for_status(self): pass
        def iter_lines(self):
            yield 'data: ' + json.dumps({"choices": [{"delta": {"content": "par"}}]})
            raise httpx.ReadError("mid-stream drop")

    monkeypatch.setattr("core.provider.httpx.Client",
                        lambda *a, **k: FakeClient(lambda *a2, **k2: MidFailResp()))
    events = list(pool.chat_stream([{"role": "user", "content": "hi"}]))
    assert events[-1]["type"] == "error"
    assert any(e["type"] == "chunk" for e in events)
