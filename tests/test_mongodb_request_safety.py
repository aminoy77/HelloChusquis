"""Regression tests for safe MongoDB HTTP gateway requests."""

import unittest

from tools import mongodb


class TestMongoDBRequestSafety(unittest.TestCase):
    def test_rejects_non_public_or_non_https_mongodb_gateway_urls(self):
        with self.assertRaises(ValueError):
            mongodb._api_base("http://127.0.0.1:8080")
        with self.assertRaises(ValueError):
            mongodb._api_base("https://localhost:8080")

    def test_bounds_requested_document_count(self):
        self.assertEqual(mongodb._bounded_limit(999999), 100)
        self.assertEqual(mongodb._bounded_limit(-1), 1)


if __name__ == "__main__":
    unittest.main()
