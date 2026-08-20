"""Regression tests for bounded finished process session retention."""

import unittest

from tools.shell import ProcessManager, ProcessSession, ProcessStatus


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


if __name__ == "__main__":
    unittest.main()
