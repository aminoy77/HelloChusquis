"""Regression tests for collision-resistant non-protocol tool hashes."""

import hashlib
import unittest
from unittest.mock import patch

from tools import embeddings, websearch


class TestToolHashSecurity(unittest.TestCase):
    def test_websearch_cache_key_uses_sha256_length(self):
        key = websearch._cache_key("query", 5, "", "")

        self.assertEqual(len(key), 64)
        self.assertEqual(key, websearch._cache_key("query", 5, "", ""))

    def test_demo_embedding_does_not_use_md5(self):
        with patch.object(hashlib, "md5", side_effect=AssertionError("MD5 must not be used")):
            result = embeddings.run("create", text="example")

        self.assertIn("Generated 384-dim embedding", result)


if __name__ == "__main__":
    unittest.main()
