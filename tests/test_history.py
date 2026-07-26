"""Tests for core.history — History class."""
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.history import History


class TestHistoryAddAndGet(unittest.TestCase):
    """Add messages, verify get returns them."""

    def test_add_single_message(self):
        h = History()
        h.add("user", "hello")
        msgs = h.get()
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]["role"], "user")
        self.assertEqual(msgs[0]["content"], "hello")

    def test_add_multiple_messages(self):
        h = History()
        h.add("user", "first")
        h.add("assistant", "second")
        h.add("user", "third")
        msgs = h.get()
        self.assertEqual(len(msgs), 3)
        self.assertEqual(msgs[0]["role"], "user")
        self.assertEqual(msgs[1]["role"], "assistant")
        self.assertEqual(msgs[2]["role"], "user")

    def test_add_system_message(self):
        h = History()
        h.add("user", "hi")
        h.add_system_message("you are helpful")
        msgs = h.get()
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[0]["role"], "system")
        self.assertEqual(msgs[0]["content"], "you are helpful")
        self.assertEqual(msgs[1]["role"], "user")


class TestHistoryClear(unittest.TestCase):
    """Add messages, clear, verify empty."""

    def test_clear(self):
        h = History()
        h.add("user", "a")
        h.add("assistant", "b")
        h.clear()
        self.assertEqual(h.get(), [])
        self.assertEqual(len(h._timestamps), 0)


class TestHistoryMaxEntries(unittest.TestCase):
    """Add >100 messages, verify oldest trimmed."""

    def test_max_entries_default(self):
        h = History()  # max_entries=100
        for i in range(105):
            h.add("user", f"msg {i}")
        msgs = h.get()
        self.assertEqual(len(msgs), 100)
        # First message should be msg 5 (oldest kept)
        self.assertEqual(msgs[0]["content"], "msg 5")

    def test_max_entries_custom(self):
        h = History(max_entries=10)
        for i in range(15):
            h.add("user", f"msg {i}")
        msgs = h.get()
        self.assertEqual(len(msgs), 10)
        self.assertEqual(msgs[0]["content"], "msg 5")

    def test_max_entries_preserves_system(self):
        h = History(max_entries=5)
        h.add_system_message("system prompt")
        for i in range(10):
            h.add("user", f"msg {i}")
        msgs = h.get()
        self.assertLessEqual(len(msgs), 5)
        self.assertEqual(msgs[0]["role"], "system")
        self.assertEqual(msgs[0]["content"], "system prompt")


class TestHistoryCompressIfNeeded(unittest.TestCase):
    """Add many messages, compress, verify system + last 5 kept."""

    def test_compress_when_over_budget(self):
        h = History()
        h.add_system_message("You are a helpful assistant.")
        # Add 20 long messages to blow past any token budget
        for i in range(20):
            h.add("user", "x " * 200)
            h.add("assistant", "y " * 200)
        result = h.compress_if_needed(max_tokens=10)
        # System message should be first
        self.assertEqual(result[0]["role"], "system")
        # Last 5 messages should be preserved in full
        self.assertGreaterEqual(len(result), 5)

    def test_compress_when_under_budget(self):
        h = History()
        h.add("user", "short")
        h.add("assistant", "reply")
        result = h.compress_if_needed(max_tokens=100000)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["content"], "short")


class TestHistoryGetStats(unittest.TestCase):
    """Verify stats dict has correct keys."""

    def test_stats_keys(self):
        h = History()
        h.add("user", "hello world")
        stats = h.get_stats()
        self.assertIn("total_messages", stats)
        self.assertIn("total_tokens", stats)
        self.assertIn("oldest_timestamp", stats)

    def test_stats_values(self):
        h = History()
        h.add("user", "hello")
        stats = h.get_stats()
        self.assertEqual(stats["total_messages"], 1)
        self.assertIsInstance(stats["total_tokens"], int)
        self.assertIsNotNone(stats["oldest_timestamp"])

    def test_stats_empty_history(self):
        h = History()
        stats = h.get_stats()
        self.assertEqual(stats["total_messages"], 0)
        self.assertIsNone(stats["oldest_timestamp"])


if __name__ == "__main__":
    unittest.main()
