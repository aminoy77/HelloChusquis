"""HTTP regression tests for costly administrative endpoint rate limits."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from api import main as api_main
from core.rate_limiter import RateLimiter
from web import server as web_server


class TestAdministrativeRateLimits(unittest.TestCase):
    def setUp(self):
        self.limiters = []

    def tearDown(self):
        for limiter in self.limiters:
            limiter.close()

    def _one_request_limiter(self):
        limiter = RateLimiter(requests_per_minute=1, cleanup_interval=60.0)
        self.limiters.append(limiter)
        return limiter

    @staticmethod
    def _assert_rate_limited(response):
        assert response.status_code == 429
        assert response.json()["detail"] == "Too many administrative requests"
        assert int(response.headers["retry-after"]) >= 1

    def test_api_runtime_reload_returns_429_after_limit(self):
        limiter = self._one_request_limiter()
        with patch.object(api_main, "_reload_limiter", limiter), patch.object(
            api_main.runtime, "refresh", return_value=False
        ):
            client = TestClient(api_main.app)
            headers = {"Authorization": f"Bearer {api_main.REQUIRED_API_KEY}"}
            self.assertEqual(client.post("/runtime/reload", headers=headers).status_code, 503)
            self._assert_rate_limited(client.post("/runtime/reload", headers=headers))

    def test_web_runtime_reload_returns_429_after_limit(self):
        limiter = self._one_request_limiter()
        with patch.object(web_server, "_reload_limiter", limiter), patch.object(
            web_server.runtime, "refresh", return_value=False
        ):
            client = TestClient(web_server.app)
            headers = {"Authorization": f"Bearer {web_server.REQUIRED_API_KEY}"}
            self.assertEqual(client.post("/runtime/reload", headers=headers).status_code, 503)
            self._assert_rate_limited(client.post("/runtime/reload", headers=headers))

    def test_web_provider_update_returns_429_after_limit(self):
        limiter = self._one_request_limiter()
        with patch.object(web_server, "_provider_update_limiter", limiter):
            client = TestClient(web_server.app)
            headers = {
                "Authorization": f"Bearer {web_server.REQUIRED_API_KEY}",
                "X-HelloChusquis-Session": "admin-session",
            }
            payload = {"name": "any-provider"}
            self.assertEqual(client.post("/update-provider", json=payload, headers=headers).status_code, 503)
            self._assert_rate_limited(client.post("/update-provider", json=payload, headers=headers))

    def test_forced_model_refresh_returns_429_before_second_provider_call(self):
        general_limiter = self._one_request_limiter()
        refresh_limiter = self._one_request_limiter()
        pool = SimpleNamespace(
            status=lambda: [{"name": "Test Provider"}],
            list_models=Mock(return_value=["test-model"]),
        )
        agent = SimpleNamespace(pool=pool)
        headers = {
            "Authorization": f"Bearer {web_server.REQUIRED_API_KEY}",
            "X-HelloChusquis-Session": "models-session",
        }
        with patch.object(web_server, "_models_limiter", general_limiter), patch.object(
            web_server, "_models_refresh_limiter", refresh_limiter
        ), patch.object(web_server, "_require_agent", return_value=agent):
            client = TestClient(web_server.app)
            first = client.get("/models?provider=Test%20Provider&refresh=true", headers=headers)
            self.assertEqual(first.status_code, 200)
            self._assert_rate_limited(
                client.get("/models?provider=Test%20Provider&refresh=true", headers=headers)
            )

        pool.list_models.assert_called_once_with("Test Provider", refresh=True)


if __name__ == "__main__":
    unittest.main()
