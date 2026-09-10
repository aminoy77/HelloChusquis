"""Failover: repeated network failures exhaust a provider; success resets."""
import unittest
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx
from core.provider import ProviderPool


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


class TestNetworkExhaustion(unittest.TestCase):
    def test_two_network_failures_exhaust(self):
        pool = _pool()
        with patch.object(pool, "_call", side_effect=httpx.ConnectError("down")):
            with self.assertRaises(RuntimeError):
                pool.chat([{"role": "user", "content": "hi"}])
            with self.assertRaises(RuntimeError):
                pool.chat([{"role": "user", "content": "hi"}])
        self.assertEqual(pool._available(), [])

    def test_success_resets_failure_count(self):
        pool = _pool()
        pool.providers[0].failed_calls = 5
        with patch.object(pool, "_call", return_value={"choices": []}):
            pool.chat([{"role": "user", "content": "hi"}])
        self.assertEqual(pool.providers[0].failed_calls, 0)
        self.assertEqual(len(pool._available()), 1)


if __name__ == "__main__":
    unittest.main()
