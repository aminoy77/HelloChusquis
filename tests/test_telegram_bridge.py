"""Tests for the Telegram bridge (core/telegram_bridge.py). No network."""
import pytest


class FakeTransport:
    """Scripted Bot API: pops getUpdates payloads, records sendMessage calls."""

    def __init__(self, updates):
        self.updates = list(updates)
        self.sent = []

    def __call__(self, method, params):
        if method == "getUpdates":
            return {"ok": True, "result": self.updates.pop(0) if self.updates else []}
        if method == "sendMessage":
            self.sent.append(params)
            return {"ok": True, "result": {"message_id": len(self.sent)}}
        raise AssertionError(f"unexpected method {method}")


def _msg(update_id, chat_id, text):
    return {"update_id": update_id,
            "message": {"message_id": 1, "chat": {"id": chat_id, "type": "private"},
                        "text": text}}


def test_run_once_dispatches_and_replies():
    from core.telegram_bridge import TelegramBridge
    t = FakeTransport([[ _msg(10, 123, "hola") ]])
    b = TelegramBridge(t, lambda chat, text: f"echo:{text}", allow_chats={123})
    b.run_once()
    assert t.sent == [{"chat_id": 123, "text": "echo:hola"}]
    assert b.offset == 11


def test_unauthorized_chat_ignored_but_offset_advances():
    from core.telegram_bridge import TelegramBridge
    t = FakeTransport([[ _msg(10, 999, "hola") ]])
    b = TelegramBridge(t, lambda chat, text: "never", allow_chats={123})
    b.run_once()
    assert t.sent == []
    assert b.offset == 11


def test_long_reply_split_at_limit():
    from core.telegram_bridge import TelegramBridge
    t = FakeTransport([[ _msg(10, 123, "go") ]])
    b = TelegramBridge(t, lambda chat, text: "x" * 5000, allow_chats={123})
    b.run_once()
    assert len(t.sent) == 2
    assert all(len(s["text"]) <= 4096 for s in t.sent)
    assert "".join(s["text"] for s in t.sent) == "x" * 5000


def test_non_text_and_empty_updates_no_crash():
    from core.telegram_bridge import TelegramBridge
    t = FakeTransport([[ {"update_id": 10, "message": {"message_id": 2, "chat": {"id": 123}}} ], []])
    b = TelegramBridge(t, lambda chat, text: "never", allow_chats={123})
    b.run_once()
    b.run_once()
    assert t.sent == []
    assert b.offset == 11


def test_handler_error_replies_gracefully():
    from core.telegram_bridge import TelegramBridge
    def boom(chat, text):
        raise RuntimeError("agent down")
    t = FakeTransport([[ _msg(10, 123, "hi") ]])
    b = TelegramBridge(t, boom, allow_chats={123})
    b.run_once()
    assert len(t.sent) == 1
    assert "could not be completed" in t.sent[0]["text"].lower()


def test_run_forever_backs_off_and_stops():
    import threading
    from core.telegram_bridge import TelegramBridge
    calls = {"n": 0}

    def flaky(method, params):
        calls["n"] += 1
        if calls["n"] == 1:
            raise ConnectionError("net down")
        return {"ok": True, "result": []}

    b = TelegramBridge(flaky, lambda c, t: "x", allow_chats={1}, backoff_s=0.01)
    stop = threading.Event()
    import time

    def stopper():
        time.sleep(0.15)
        stop.set()
    threading.Thread(target=stopper, daemon=True).start()
    b.run_forever(stop)  # must not raise
    assert calls["n"] >= 2
