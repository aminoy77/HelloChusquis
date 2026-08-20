"""Regression tests for durable, concurrent local learning persistence."""

import json
from pathlib import Path
import stat
import tempfile
import threading
import unittest
from unittest.mock import patch

from core import learning


class TestLearningPersistence(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.learning_dir = Path(self.temporary_directory.name) / "learnings"
        self.learning_file = self.learning_dir / "learnings.json"
        self.patches = [
            patch.object(learning, "LEARNING_DIR", self.learning_dir),
            patch.object(learning, "LEARNING_FILE", self.learning_file),
        ]
        for patcher in self.patches:
            patcher.start()

    def tearDown(self):
        for patcher in reversed(self.patches):
            patcher.stop()
        self.temporary_directory.cleanup()

    def test_initial_storage_has_owner_only_permissions(self):
        learning.init()

        self.assertEqual(stat.S_IMODE(self.learning_dir.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(self.learning_file.stat().st_mode), 0o600)
        self.assertEqual(json.loads(self.learning_file.read_text())["feedback"], {"positive": [], "negative": []})

    def test_concurrent_feedback_updates_are_preserved(self):
        workers = 24
        start = threading.Barrier(workers)
        failures = []

        def write_feedback(index):
            try:
                start.wait()
                learning.add_feedback("positive", f"feedback-{index}")
            except Exception as exc:  # pragma: no cover - asserted through failures
                failures.append(exc)

        threads = [threading.Thread(target=write_feedback, args=(index,)) for index in range(workers)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(failures, [])
        entries = learning.load_learnings()["feedback"]["positive"]
        self.assertEqual(len(entries), workers)
        self.assertEqual({entry["context"] for entry in entries}, {f"feedback-{index}" for index in range(workers)})

    def test_feedback_retention_stays_bounded(self):
        for index in range(60):
            learning.add_feedback("negative", f"feedback-{index}")

        entries = learning.load_learnings()["feedback"]["negative"]
        self.assertEqual(len(entries), 50)
        self.assertEqual(entries[0]["context"], "feedback-10")
        self.assertEqual(entries[-1]["context"], "feedback-59")


if __name__ == "__main__":
    unittest.main()
