"""Telegram bridge: talk to HelloChusquis from Telegram. Standard library only.

Security: the bot answers ONLY allowlisted chat IDs (fail-fast without them).
The token never leaves memory except inside HTTPS calls to api.telegram.org.
"""
from __future__ import annotations

import json
import logging
import threading
import urllib.request
from typing import Callable

from core.logger import get_logger

logger = get_logger("telegram")

MAX_TEXT = 4096  # Telegram sendMessage limit


class TelegramAPI:
    """Minimal Bot API client (getUpdates long-poll + sendMessage)."""

    def __init__(self, token: str, request_fn: Callable | None = None):
        self.token = token
        self._request_fn = request_fn

    def call(self, method: str, params: dict) -> dict:
        if self._request_fn is not None:
            return self._request_fn(method, params)
        data = json.dumps(params).encode("utf-8")
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{self.token}/{method}",
            data=data, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=70) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def get_updates(self, offset: int, timeout: int) -> list:
        payload = self.call("getUpdates", {"offset": offset, "timeout": timeout,
                                           "allowed_updates": ["message"]})
        if not payload.get("ok"):
            raise RuntimeError(f"getUpdates failed: {payload}")
        return payload.get("result", [])

    def send_message(self, chat_id: int, text: str) -> None:
        payload = self.call("sendMessage", {"chat_id": chat_id, "text": text})
        if not payload.get("ok"):
            raise RuntimeError(f"sendMessage failed: {payload}")


def split_message(text: str, limit: int = MAX_TEXT) -> list:
    """Split long texts on line boundaries (hard-cut oversized lines)."""
    if len(text) <= limit:
        return [text]
    parts, cur, cur_len = [], [], 0
    for line in text.splitlines(keepends=True):
        if len(line) > limit:
            if cur:
                parts.append("".join(cur))
                cur, cur_len = [], 0
            parts.extend(line[i:i + limit] for i in range(0, len(line), limit))
        elif cur_len + len(line) > limit:
            parts.append("".join(cur))
            cur, cur_len = [line], len(line)
        else:
            cur.append(line)
            cur_len += len(line)
    if cur:
        parts.append("".join(cur))
    return parts or [text]


class TelegramBridge:
    """Poll loop. `transport(method, params)` + `handle_text(chat_id, text) -> str` injected."""

    def __init__(self, transport: Callable, handle_text: Callable,
                 allow_chats, poll_timeout: int = 25, backoff_s: float = 5.0):
        self.transport = transport
        self.handle_text = handle_text
        self.allow = {int(c) for c in (allow_chats or [])}
        self.poll_timeout = poll_timeout
        self.backoff_s = backoff_s
        self.offset = 0

    def _api(self, method: str, params: dict) -> dict:
        fn = getattr(self.transport, "call", None)
        if callable(fn):
            return fn(method, params)
        return self.transport(method, params)

    def run_once(self) -> None:
        updates = self._api("getUpdates", {"offset": self.offset,
                                           "timeout": self.poll_timeout,
                                           "allowed_updates": ["message"]})
        results = updates.get("result", []) if isinstance(updates, dict) else updates
        for update in results or []:
            try:
                self.offset = max(self.offset, int(update.get("update_id", -1)) + 1)
            except (TypeError, ValueError):
                continue
            msg = update.get("message") or {}
            text = msg.get("text", "")
            chat_id = (msg.get("chat") or {}).get("id")
            if not isinstance(text, str) or not text.strip() or chat_id is None:
                continue
            try:
                chat_id = int(chat_id)
            except (TypeError, ValueError):
                continue
            if chat_id not in self.allow:
                logger.warning("Ignoring Telegram message from unauthorized chat %s", chat_id)
                continue
            try:
                reply = self.handle_text(chat_id, text.strip()) or ""
            except Exception:
                logger.exception("Telegram handler failed for chat %s", chat_id)
                reply = "The request could not be completed. Check server logs."
            if not reply.strip():
                reply = "(empty response)"
            for chunk in split_message(reply):
                try:
                    self._api("sendMessage", {"chat_id": chat_id, "text": chunk})
                except Exception:
                    logger.exception("Telegram send failed for chat %s", chat_id)

    def run_forever(self, stop: threading.Event | None = None) -> None:
        waiter = stop if stop is not None else threading.Event()
        while not waiter.is_set():
            try:
                self.run_once()
            except KeyboardInterrupt:
                raise
            except Exception:
                logger.exception("Telegram poll failed; retrying in %ss", self.backoff_s)
                waiter.wait(self.backoff_s)
