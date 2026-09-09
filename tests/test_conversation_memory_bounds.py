"""Regression tests for bounded legacy conversation-memory queries."""

import tempfile
import unittest
from pathlib import Path

from core.conversation_memory import ConversationMemory


class TestConversationMemoryBounds(unittest.TestCase):
    def test_negative_search_limit_cannot_return_an_unbounded_result_set(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = ConversationMemory(str(Path(directory) / "memory.db"))
            for index in range(10):
                memory.remember(f"key-{index}", "matching value")

            self.assertEqual(len(memory.search("matching", limit=-1)), 1)


if __name__ == "__main__":
    unittest.main()
