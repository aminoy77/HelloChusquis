"""Regression tests for global HTTP request body limits."""

import unittest

from fastapi.testclient import TestClient

from api import main as api_main
from web import server as web_server


class TestRequestBodyLimits(unittest.TestCase):
    @staticmethod
    def _oversized_body(module):
        return b"x" * (module.MAX_REQUEST_BODY_BYTES + 1)

    def test_api_rejects_oversized_authenticated_body(self):
        response = TestClient(api_main.app).post(
            "/feedback",
            content=self._oversized_body(api_main),
            headers={
                "Authorization": f"Bearer {api_main.REQUIRED_API_KEY}",
                "Content-Type": "application/json",
            },
        )

        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json()["detail"], "Request body too large")
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_web_rejects_oversized_public_auth_body(self):
        response = TestClient(web_server.app).post(
            "/auth/verify",
            content=self._oversized_body(web_server),
            headers={"Content-Type": "application/json"},
        )

        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json()["detail"], "Request body too large")
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["x-frame-options"], "DENY")

    def test_normal_sized_requests_continue_to_reach_handlers(self):
        web_response = TestClient(web_server.app).post(
            "/auth/verify",
            json={"message": web_server.REQUIRED_API_KEY},
        )
        api_response = TestClient(api_main.app).post(
            "/feedback",
            json={"type": "positive", "context": "normal"},
            headers={"Authorization": f"Bearer {api_main.REQUIRED_API_KEY}"},
        )

        self.assertEqual(web_response.status_code, 200)
        self.assertEqual(api_response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
