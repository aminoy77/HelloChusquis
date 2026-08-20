"""Regression tests for session-scoped provider endpoints."""

from types import SimpleNamespace
import unittest
from unittest.mock import patch

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


class TestProviderSessionScope(unittest.TestCase):
    def setUp(self):
        self.request = SimpleNamespace(headers={"x-hellochusquis-session": "session-a"})
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


if __name__ == "__main__":
    unittest.main()
