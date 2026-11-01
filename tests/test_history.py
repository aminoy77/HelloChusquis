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

    def test_clear(self):
        h = History()
        h.add("user", "a")
        h.add("assistant", "b")
        h.clear()
        self.assertEqual(h.get(), [])
        self.assertEqual(len(h._timestamps), 0)


class TestHistoryMaxEntries(unittest.TestCase):
    """Add >100 messages, verify oldest trimmed."""

    def test_max_entries_one_does_not_exceed_bound_with_system_message(self):
        h = History(max_entries=1)
        h.add("system", "system")
        h.add("user", "first")
        h.add("assistant", "second")

        self.assertEqual(h.get(), [{"role": "system", "content": "system"}])
        self.assertEqual(len(h.get()), 1)

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
        h.add("system", "system prompt")
        for i in range(10):
            h.add("user", f"msg {i}")
        msgs = h.get()
        self.assertLessEqual(len(msgs), 5)
        self.assertEqual(msgs[0]["role"], "system")
        self.assertEqual(msgs[0]["content"], "system prompt")


class TestHistoryCompressIfNeeded(unittest.TestCase):
    """Add many messages, compress, verify system + last 5 kept."""

