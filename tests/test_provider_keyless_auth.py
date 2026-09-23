"""Keyless local providers (Ollama, LM Studio) must not send an empty Bearer header."""
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.provider import Provider, ProviderPool


class FakeResponse:
    def raise_for_status(self):
        pass

    def json(self):
        return {"choices": [{"message": {"content": "ok"}}]}


class FakeClient:
    last_headers = None

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, url, headers=None, json=None):
        FakeClient.last_headers = headers
        return FakeResponse()


def _pool(provider):
    pool = ProviderPool.__new__(ProviderPool)
    pool.providers = [provider]
    pool.timeout = 15.0
    return pool


class TestKeylessAuth(unittest.TestCase):
    def _call(self, api_key):
        provider = Provider(name="Ollama", base_url="http://localhost:11434/v1",
                            api_key=api_key, model="llama3.2:1b", priority=1)
        with patch("core.provider.httpx.Client", FakeClient):
            _pool(provider)._call(provider, [{"role": "user", "content": "hi"}], None)
        return FakeClient.last_headers

    def test_empty_key_sends_no_auth_header(self):
        for key in ("", "   ", None):
            headers = self._call(key)
            self.assertNotIn("Authorization", headers)

    def test_key_sends_bearer(self):
        headers = self._call("sk-test")
        self.assertEqual(headers.get("Authorization"), "Bearer sk-test")


if __name__ == "__main__":
    unittest.main()
