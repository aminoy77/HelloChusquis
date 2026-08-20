"""Regression tests for legacy session persistence collisions."""

import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from core import memory


class TestLegacyMemorySessions(unittest.TestCase):
    def test_sessions_saved_in_same_second_receive_distinct_files(self):
        fixed_now = datetime(2026, 8, 20, 12, 0, 0)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (
                patch.object(memory, "MEMORY_DIR", root),
                patch.object(memory, "SESSIONS_DIR", root / "sessions"),
                patch.object(memory, "MEMORY_FILE", root / "memory.json"),
                patch("core.memory.datetime") as mocked_datetime,
            ):
                mocked_datetime.now.return_value = fixed_now
                memory.save_session([{"role": "user", "content": "first"}])
                memory.save_session([{"role": "user", "content": "second"}])

            files = list((root / "sessions").glob("*.json"))
            self.assertEqual(len(files), 2)


if __name__ == "__main__":
    unittest.main()
