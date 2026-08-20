"""Regression tests for the generic HTTP client's network safety controls."""

import unittest

from tools import http as http_tool
from tools.web_fetch import SsrFBlockedError


class TestHttpSsrfSafety(unittest.TestCase):
    def test_generic_http_client_reuses_shared_ssrf_validation(self):
        self.assertEqual(http_tool._safe_url("https://8.8.8.8/public"), "https://8.8.8.8/public")
        with self.assertRaises(SsrFBlockedError):
            http_tool._safe_url("http://127.0.0.1:8080/admin")


if __name__ == "__main__":
    unittest.main()
