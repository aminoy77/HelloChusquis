"""Failover: repeated network failures exhaust a provider; success resets."""
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

    def test_pinned_provider_falls_back_to_others(self):
        pool = _pool()
        pool.providers.append(Provider(
            name="P2", base_url="http://127.0.0.1:9/v1", api_key="k",
            model="m2", priority=2))
        calls = []

        def fake_call(provider, messages, tools, model=None):
            calls.append((provider.name, model))
            if provider.name == "P1":
                raise httpx.HTTPStatusError(
                    "bad", request=None,
                    response=httpx.Response(401, json={"error": {"message": "no"}}))
            return {"choices": []}

        with patch.object(pool, "_call", side_effect=fake_call):
            pool.chat([{"role": "user", "content": "hi"}],
                      provider_name="P1", model="m1")
        self.assertEqual([c[0] for c in calls], ["P1", "P2"])
        # P2 keeps its own model; the pinned model must not leak onto it.
        self.assertEqual(calls[1][1], None)


if __name__ == "__main__":
    unittest.main()
