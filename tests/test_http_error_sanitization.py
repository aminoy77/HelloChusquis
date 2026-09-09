"""Public HTTP errors must not include internal exception details."""

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api import main as api_main
from core.rate_limiter import RateLimiter
from core.runtime import AgentNotReadyError
from web import server as web_server

_SECRET_DETAIL = "internal-path:/private/config.yaml"


class _FailingChatAgent:
    def try_acquire_turn(self):
        return True

    def run(self, *_args, **_kwargs):
        raise RuntimeError(_SECRET_DETAIL)

    def release_turn(self):
        pass


class _MissingApprovalAgent:
    def try_acquire_turn(self):
        return True

    def release_turn(self):
        pass

    def decide_approval(self, *_args, **_kwargs):
        raise KeyError(_SECRET_DETAIL)


class TestHttpErrorSanitization(unittest.TestCase):
    def setUp(self):
        self.limiters = []

    def tearDown(self):
        for limiter in self.limiters:
            limiter.close()

    @staticmethod
    def _headers(module, session="error-sanitization"):
        return {
            "Authorization": f"Bearer {module.REQUIRED_API_KEY}",
            "X-HelloChusquis-Session": session,
        }

    def _reload_limiter(self):
        limiter = RateLimiter(requests_per_minute=1, cleanup_interval=60.0)
        self.limiters.append(limiter)
        return limiter

    def test_agent_not_ready_error_is_sanitized_on_both_http_surfaces(self):
        for module in (api_main, web_server):
            with self.subTest(module=module.__name__), patch.object(
                module.runtime, "get", side_effect=AgentNotReadyError(_SECRET_DETAIL)
            ):
                response = TestClient(module.app).get("/approvals", headers=self._headers(module))

            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json()["detail"], "Agent runtime is not ready. Complete setup and retry.")
            self.assertNotIn(_SECRET_DETAIL, response.text)

    def test_readiness_failure_is_sanitized_on_both_http_surfaces(self):
        for module in (api_main, web_server):
            with self.subTest(module=module.__name__), patch.object(
                module.runtime, "readiness", return_value={"ready": False, "error": _SECRET_DETAIL}
            ):
                response = TestClient(module.app).get("/health/ready")

            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json()["detail"], "No providers are ready")
            self.assertNotIn(_SECRET_DETAIL, response.text)

    def test_runtime_reload_failure_is_sanitized_on_both_http_surfaces(self):
        for module in (api_main, web_server):
            limiter = self._reload_limiter()
            with self.subTest(module=module.__name__), patch.object(
                module, "_reload_limiter", limiter
            ), patch.object(module.runtime, "refresh", return_value=False), patch.object(
                module.runtime, "_error", _SECRET_DETAIL
            ):
                response = TestClient(module.app).post("/runtime/reload", headers=self._headers(module))

            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json()["detail"], "Runtime reload failed")
            self.assertNotIn(_SECRET_DETAIL, response.text)

    def test_approval_error_is_sanitized_on_both_http_surfaces(self):
        for module in (api_main, web_server):
            with self.subTest(module=module.__name__), patch.object(
                module, "_require_agent", return_value=_MissingApprovalAgent()
            ):
                response = TestClient(module.app).post(
                    "/approvals/approval-id",
                    json={"approve": True},
                    headers=self._headers(module),
                )

            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json()["detail"], "Approval request not found")
            self.assertNotIn(_SECRET_DETAIL, response.text)

    def test_web_chat_runtime_error_is_sanitized(self):
        with patch.object(web_server, "_require_agent", return_value=_FailingChatAgent()):
            response = TestClient(web_server.app).post(
                "/chat",
                json={"message": "hello"},
                headers=self._headers(web_server),
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["response"], "The request could not be completed. Check server logs.")
        self.assertNotIn(_SECRET_DETAIL, response.text)


if __name__ == "__main__":
    unittest.main()
