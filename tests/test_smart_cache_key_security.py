"""Regression tests for collision-resistant SmartCache keys."""

import unittest

from core.smart_cache import SmartCache


class TestSmartCacheKeySecurity(unittest.TestCase):
    def test_generated_memoization_key_uses_sha256_digest_length(self):
        cache = SmartCache()
        key = cache._make_key("function", "argument", option="value")

        self.assertEqual(len(key), 64)
        self.assertEqual(key, cache._make_key("function", "argument", option="value"))


if __name__ == "__main__":
    unittest.main()
