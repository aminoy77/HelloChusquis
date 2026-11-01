"""HTTP-status exhaustion rules: 401/402/403/404/405/429 immediate, 5xx on
second consecutive failure, 400 never."""
import unittest
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx
from core.provider import Provider, ProviderPool


def _pool():
    return ProviderPool(config={
        "providers": [
            {"name": "P1", "base_url": "http://127.0.0.1:9/v1",
             "api_key": "k", "model": "m", "priority": 1},
        ],
        "settings": {"provider_reset_hours": 1, "timeout_seconds": 15,
                     "workspace_dirs": ["/tmp"]},
        "agent": {"system_prompt": "x" * 120},
    })


def _status_error(status: int) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "http://127.0.0.1:9/v1/chat/completions")
    response = httpx.Response(status, request=request)
    return httpx.HTTPStatusError(f"HTTP {status}", request=request, response=response)


class TestHttpStatusExhaustion(unittest.TestCase):
    def _chat_once(self, pool, status):
        with patch.object(pool, "_call", side_effect=_status_error(status)):
            with self.assertRaises(RuntimeError):
                pool.chat([{"role": "user", "content": "hi"}])

    def test_auth_and_quota_statuses_exhaust_immediately(self):
        for status in (401, 402, 403, 404, 405, 429):
            pool = _pool()
            self._chat_once(pool, status)
            self.assertTrue(pool.providers[0].exhausted, f"status {status} must exhaust")
            self.assertEqual(len(pool._available()), 0)

    def test_5xx_exhausts_only_on_second_consecutive_failure(self):
        pool = _pool()
        self._chat_once(pool, 500)
        self.assertFalse(pool.providers[0].exhausted)
        self.assertEqual(len(pool._available()), 1)
        self._chat_once(pool, 500)
        self.assertTrue(pool.providers[0].exhausted)
        self.assertEqual(len(pool._available()), 0)

    def test_400_never_exhausts(self):
        pool = _pool()
        for _ in range(3):
            self._chat_once(pool, 400)
        self.assertFalse(pool.providers[0].exhausted)
        self.assertEqual(len(pool._available()), 1)


if __name__ == "__main__":
    unittest.main()
