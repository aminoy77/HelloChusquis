"""HTTP security header contract tests."""

import unittest

from fastapi.testclient import TestClient

from api import main as api_main
from web import server as web_server


class TestSecurityHeaders(unittest.TestCase):
    def test_api_health_includes_baseline_security_headers(self):
        response = TestClient(api_main.app).get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["x-frame-options"], "DENY")
        self.assertEqual(response.headers["referrer-policy"], "no-referrer")
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_web_root_includes_baseline_security_headers(self):
        response = TestClient(web_server.app).get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["x-frame-options"], "DENY")
        self.assertEqual(response.headers["referrer-policy"], "no-referrer")


if __name__ == "__main__":
    unittest.main()
