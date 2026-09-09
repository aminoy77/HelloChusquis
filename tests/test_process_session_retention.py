"""Regression tests for bounded finished process session retention."""

import unittest

from tools.shell import OUTPUT_TRUNCATION_MARKER, ProcessManager, ProcessSession, ProcessStatus


class TestProcessSessionRetention(unittest.TestCase):
    def test_finished_sessions_are_bounded_by_oldest_completion(self):
        manager = ProcessManager(max_finished_sessions=2)
        try:
            for session_id in ("first", "second", "third"):
                manager._sessions[session_id] = ProcessSession(
                    id=session_id,
                    command="echo done",
                    started_at=1.0,
                    ended_at=2.0,
                    status=ProcessStatus.COMPLETED,
                )
                manager._finalize(session_id)

            self.assertEqual(
                [session.id for session in manager.list_finished()],
                ["second", "third"],
            )
        finally:
            manager.shutdown()

    def test_finished_session_limit_must_be_positive(self):
        with self.assertRaises(ValueError):
            ProcessManager(max_finished_sessions=0)

    def test_output_retention_is_byte_bounded_and_marked_as_truncated(self):
        manager = ProcessManager(max_output_bytes=48)
        try:
            session = ProcessSession(id="noisy")
            manager._append_output(session, "stdout_buffer", "prefix-" + "x" * 100)

            self.assertTrue(session.truncated)
            self.assertTrue(session.stdout_buffer.startswith(OUTPUT_TRUNCATION_MARKER))
            self.assertLessEqual(len(session.stdout_buffer.encode("utf-8")), 48)
            self.assertTrue(session.stdout_buffer.endswith("x" * 10))
        finally:
            manager.shutdown()

    def test_output_limit_must_be_positive(self):
        with self.assertRaises(ValueError):
            ProcessManager(max_output_bytes=0)


if __name__ == "__main__":
    unittest.main()
