"""Autolog memory: every turn searchable, curated facts, forget works."""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import core.db_memory as db_memory
from core.agent import extract_memory_facts, parse_memory_command


class TestMemoryAutolog(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig = db_memory.MEMORY_DB_PATH
        import pathlib
        db_memory.MEMORY_DB_PATH = pathlib.Path(self._tmpdir) / "auto.db"

    def tearDown(self):
        db_memory.MEMORY_DB_PATH = self._orig
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_turn_saved_and_recalled_next_turn(self):
        db_memory.save_turn("my dog is called Rex", "noted, Rex it is")
        block = db_memory.recall_context("what is my dog called?")
        self.assertIn("Rex", block)

    def test_forget_removes_matching_fact(self):
        db_memory.save_turn("my dog is called Rex", "noted")
        removed = db_memory.forget_matching("dog")
        self.assertGreaterEqual(removed, 1)
        self.assertNotIn("Rex", db_memory.recall_context("dog"))

    def test_extract_memory_facts_captures_preferences(self):
        facts = extract_memory_facts("my editor is vscode, I prefer dark mode")
        self.assertTrue(any("vscode" in v for _, v in facts))
        self.assertLessEqual(len(facts), 2)

    def test_parse_memory_command(self):
        self.assertEqual(parse_memory_command("remember my pin is 1234")[0], "remember")
        self.assertEqual(parse_memory_command("forget my pin")[0], "forget")
        self.assertIsNone(parse_memory_command("what did I ask before?"))


if __name__ == "__main__":
    unittest.main()
