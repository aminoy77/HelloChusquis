"""Regression tests for secure permissions in the legacy disk cache."""

import tempfile
import unittest
from pathlib import Path

from core.cache import Cache


class TestLegacyCachePermissions(unittest.TestCase):
    def test_cache_directory_and_entry_are_private(self):
        with tempfile.TemporaryDirectory() as directory:
            cache_path = Path(directory) / "cache"
            cache = Cache(str(cache_path))
            cache.set("query", "response")

            entry = next(cache_path.glob("*.json"))
            self.assertEqual(cache_path.stat().st_mode & 0o077, 0)
            self.assertEqual(entry.stat().st_mode & 0o077, 0)


if __name__ == "__main__":
    unittest.main()
