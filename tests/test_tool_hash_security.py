"""Regression tests for collision-resistant non-protocol tool hashes."""

import unittest

from tools import websearch


class TestToolHashSecurity(unittest.TestCase):
    def test_websearch_cache_key_uses_sha256_length(self):
        key = websearch._cache_key("query", 5, "", "")

        self.assertEqual(len(key), 64)
        self.assertEqual(key, websearch._cache_key("query", 5, "", ""))


if __name__ == "__main__":
    unittest.main()
