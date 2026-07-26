"""Tests for core.db_memory — SQLite session/summary storage."""
import unittest
import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import core.db_memory as db_memory


class TestDBMemory(unittest.TestCase):
    """Save/load sessions and summaries using a temp DB."""

    def setUp(self):
        """Redirect DB to a temporary file."""
        self._tmpdir = tempfile.mkdtemp()
        self._tmpdb = os.path.join(self._tmpdir, "test_memory.db")
        self._orig_path = db_memory.MEMORY_DB_PATH
        db_memory.MEMORY_DB_PATH = __import__("pathlib").Path(self._tmpdb)

    def tearDown(self):
        """Restore original path and clean up."""
        db_memory.MEMORY_DB_PATH = self._orig_path
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_save_and_load_session(self):
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
        ]
        db_memory.save_session(messages)
        loaded = db_memory.load_last_session()
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0]["role"], "user")
        self.assertEqual(loaded[1]["content"], "hi there")

    def test_save_and_load_summary(self):
        summary = "User discussed project setup and deployment."
        db_memory.save_summary(summary)
        loaded = db_memory.load_summary()
        self.assertEqual(loaded, summary)

    def test_empty_session(self):
        """Saving empty list should not error."""
        db_memory.save_session([])
        loaded = db_memory.load_last_session()
        self.assertEqual(loaded, [])

    def test_multiple_sessions(self):
        """Second save should be returned as latest."""
        db_memory.save_session([{"role": "user", "content": "first"}])
        db_memory.save_session([{"role": "user", "content": "second"}])
        loaded = db_memory.load_last_session()
        self.assertEqual(loaded[0]["content"], "second")

    def test_summary_overwrites_previous(self):
        db_memory.save_summary("first summary")
        db_memory.save_summary("second summary")
        loaded = db_memory.load_summary()
        self.assertEqual(loaded, "second summary")


if __name__ == "__main__":
    unittest.main()
