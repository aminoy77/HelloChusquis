"""Regression tests for session-scoped provider endpoints."""

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from pydantic import ValidationError

from core.identity import legacy_owner
from core.provider import ProviderPool
from web import server as web_server


class _Pool:
    def __init__(self):
        self.calls = []

    def status(self):
        return [{"name": "Test Provider", "status": "ready"}]

    def list_models(self, provider, refresh=False):
        self.calls.append(("list_models", provider, refresh))
        return ["test-model"]

    def update_api_key(self, name, key):
        self.calls.append(("key", name, key))

    def update_base_url(self, name, base):
        self.calls.append(("base", name, base))

    def update_model(self, name, model):
        self.calls.append(("model", name, model))


class _Agent:
    def __init__(self):
        self.pool = _Pool()
        self.plugins = []
        self.turn_available = True
        self.turn_acquisitions = 0
        self.turn_releases = 0

    def try_acquire_turn(self):
        if not self.turn_available:
            return False
        self.turn_available = False
        self.turn_acquisitions += 1
        return True

    def release_turn(self):
        self.turn_available = True
        self.turn_releases += 1


class TestProviderSessionScope(unittest.TestCase):
    def setUp(self):
        self.request = SimpleNamespace(
            headers={"x-hellochusquis-session": "session-a"},
            state=SimpleNamespace(principal=legacy_owner()),
        )
        self.agent = _Agent()

    def test_models_resolve_the_request_session_agent(self):
        with patch.object(web_server, "_require_agent", return_value=self.agent) as get_agent:
            response = web_server.models(self.request, provider="Test Provider")

        get_agent.assert_called_once_with(self.request)
        self.assertEqual(response["models"], ["test-model"])

    def test_status_resolves_the_request_session_agent(self):
        with patch.object(web_server.runtime, "_agent", object()), patch.object(
            web_server.runtime, "_error", None
        ), patch.object(web_server, "_require_agent", return_value=self.agent) as get_agent:
            response = web_server.status(self.request)

        get_agent.assert_called_once_with(self.request)
        self.assertEqual(response["providers"][0]["name"], "Test Provider")

    def test_provider_update_is_explicitly_session_scoped(self):
        update = web_server.ProviderUpdate(
            name="Test Provider", key="new-key", model="test-model"
        )
        with patch.object(web_server, "_require_agent", return_value=self.agent) as get_agent:
            response = web_server.update_provider(update, self.request)

        get_agent.assert_called_once_with(self.request)
        self.assertEqual(response["scope"], "session")
        self.assertIn(("key", "Test Provider", "new-key"), self.agent.pool.calls)
        self.assertIn(("model", "Test Provider", "test-model"), self.agent.pool.calls)
        self.assertEqual(self.agent.turn_acquisitions, 1)
        self.assertEqual(self.agent.turn_releases, 1)
        self.assertTrue(self.agent.turn_available)

    def test_provider_update_does_not_mutate_during_active_session_turn(self):
        self.agent.turn_available = False
        update = web_server.ProviderUpdate(name="Test Provider", key="new-key")
        with patch.object(web_server, "_require_agent", return_value=self.agent):
            with self.assertRaises(HTTPException) as raised:
                web_server.update_provider(update, self.request)

        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(self.agent.pool.calls, [])
        self.assertEqual(self.agent.turn_acquisitions, 0)
        self.assertEqual(self.agent.turn_releases, 0)

    def test_provider_update_rejects_url_with_embedded_credentials(self):
        update = web_server.ProviderUpdate(
            name="Test Provider", base="https://user:top-secret@example.test/v1"
        )
        with patch.object(web_server, "_require_agent", return_value=self.agent):
            with self.assertRaises(HTTPException) as raised:
                web_server.update_provider(update, self.request)

        self.assertEqual(raised.exception.status_code, 400)
        self.assertEqual(self.agent.pool.calls, [])
        self.assertEqual(self.agent.turn_acquisitions, 0)

    def test_provider_update_bounds_all_free_text_fields(self):
        with self.assertRaises(ValidationError):
            web_server.ProviderUpdate(name="p" * 201)
        with self.assertRaises(ValidationError):
            web_server.ProviderUpdate(name="Test Provider", key="k" * 4097)
        with self.assertRaises(ValidationError):
            web_server.ProviderUpdate(name="Test Provider", base="h" * 2049)
        with self.assertRaises(ValidationError):
            web_server.ProviderUpdate(name="Test Provider", model="m" * 257)

    def test_provider_status_redacts_legacy_url_credentials_and_query(self):
        pool = ProviderPool(
            config={
                "providers": [
                    {
                        "name": "Test Provider",
                        "base_url": "https://example.test/v1",
                        "api_key": "key",
                        "model": "test-model",
                    }
                ]
            }
        )
        pool.providers[0].base_url = "https://user:top-secret@example.test/v1?token=also-secret"

        status = pool.status()[0]

        self.assertEqual(status["base_url"], "https://example.test/v1")
        self.assertNotIn("top-secret", status["base_url"])
        self.assertNotIn("also-secret", status["base_url"])


if __name__ == "__main__":
    unittest.main()
