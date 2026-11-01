"""Regression tests for the shared SSRF validation used by every network tool."""

import unittest

from tools.web_fetch import SsrFBlockedError, validate_url_safety


class TestHttpSsrfSafety(unittest.TestCase):
    def test_validate_url_safety_allows_public_and_blocks_loopback(self):
        self.assertEqual(validate_url_safety("https://8.8.8.8/public"), "https://8.8.8.8/public")
        with self.assertRaises(SsrFBlockedError):
            validate_url_safety("http://127.0.0.1:8080/admin")


if __name__ == "__main__":
    unittest.main()
