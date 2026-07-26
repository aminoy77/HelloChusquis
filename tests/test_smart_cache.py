"""Tests for core.smart_cache — SmartCache class."""
import unittest
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.smart_cache import SmartCache


class TestSmartCacheSetAndGet(unittest.TestCase):
    """Basic cache set/get operation."""

    def test_set_and_get(self):
        c = SmartCache(max_size=10)
        c.set("k1", "value1")
        self.assertEqual(c.get("k1"), "value1")

    def test_get_missing_key(self):
        c = SmartCache()
        self.assertIsNone(c.get("nonexistent"))

    def test_overwrite(self):
        c = SmartCache()
        c.set("k", "old")
        c.set("k", "new")
        self.assertEqual(c.get("k"), "new")

    def test_remember(self):
        c = SmartCache()
        result = c.remember("k", 42)
        self.assertEqual(result, 42)
        self.assertEqual(c.get("k"), 42)


class TestSmartCacheTTLExpiry(unittest.TestCase):
    """TTL expiry behavior."""

    def test_ttl_zero_expires_immediately(self):
        c = SmartCache()
        c.set("k", "v", ttl=0)
        time.sleep(0.01)
        self.assertIsNone(c.get("k"))

    def test_ttl_long_lives(self):
        c = SmartCache()
        c.set("k", "v", ttl=60)
        self.assertEqual(c.get("k"), "v")

    def test_no_ttl_never_expires(self):
        c = SmartCache()
        c.set("k", "v")
        self.assertEqual(c.get("k"), "v")


class TestSmartCacheLRUEviction(unittest.TestCase):
    """LRU eviction when cache is full."""

    def test_evicts_oldest(self):
        c = SmartCache(max_size=3)
        c.set("a", 1)
        time.sleep(0.01)
        c.set("b", 2)
        time.sleep(0.01)
        c.set("c", 3)
        # Cache full. Adding d should evict "a" (oldest)
        c.set("d", 4)
        self.assertIsNone(c.get("a"))
        self.assertEqual(c.get("b"), 2)
        self.assertEqual(c.get("d"), 4)

    def test_lru_eviction_order(self):
        """Eviction targets oldest created_at entry."""
        c = SmartCache(max_size=3)
        c.set("a", 1)
        time.sleep(0.01)
        c.set("b", 2)
        time.sleep(0.01)
        c.set("c", 3)
        # All 3 slots full. Insert d → evicts "a" (oldest created_at)
        c.set("d", 4)
        self.assertIsNone(c.get("a"))
        self.assertEqual(c.get("b"), 2)
        self.assertEqual(c.get("c"), 3)
        self.assertEqual(c.get("d"), 4)


class TestSmartCacheStats(unittest.TestCase):
    """Hit/miss tracking in stats."""

    def test_stats_hit_miss(self):
        c = SmartCache()
        c.set("k", "v")
        c.get("k")       # hit
        c.get("miss")    # miss
        stats = c.stats()
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["size"], 1)
        self.assertEqual(stats["max_size"], c.max_size)
        self.assertIn("%", stats["hit_rate"])

    def test_stats_empty(self):
        c = SmartCache()
        stats = c.stats()
        self.assertEqual(stats["hits"], 0)
        self.assertEqual(stats["misses"], 0)

    def test_clear_resets_stats(self):
        c = SmartCache()
        c.set("k", "v")
        c.get("k")
        c.clear()
        stats = c.stats()
        self.assertEqual(stats["hits"], 0)
        self.assertEqual(stats["misses"], 0)
        self.assertEqual(stats["size"], 0)


if __name__ == "__main__":
    unittest.main()
