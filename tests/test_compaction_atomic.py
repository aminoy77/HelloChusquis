"""Audit #3: compaction must be atomic — a crash between clear and re-append
must not truncate the conversation."""
import os
import sys
import tempfile
import unittest
import unittest.mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.session import SessionManager


class TestCompactionAtomic(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "sessions.db")
        self.mgr = SessionManager(self.db)
        self.sid = self.mgr.create_session(agent_id="t", model="m")
        for i in range(5):
            self.mgr.append_message(self.sid, "user", f"msg {i}")

    def tearDown(self):
        try:
            os.remove(self.db)
        except OSError:
            pass

    def test_replace_history_is_atomic(self):
        """replace_history swaps all messages in one transaction."""
        compacted = [
            {"role": "user", "content": "summary of old"},
            {"role": "assistant", "content": "ok"},
        ]
        self.mgr.replace_history(self.sid, compacted)
        history = self.mgr.get_history(self.sid)
        self.assertEqual([m["content"] for m in history],
                         ["summary of old", "ok"])

    def test_failed_write_keeps_old_history(self):
        """If a re-append raises mid-way, the old history must survive."""
        compacted = [
            {"role": "user", "content": "summary of old"},
            {"role": "assistant", "content": "ok"},
        ]
        import core.session as session_mod
        original = session_mod.estimate_tokens

        def exploding_estimate(content):
            if content == "ok":
                raise RuntimeError("disk full")
            return original(content)

        with unittest.mock.patch.object(session_mod, "estimate_tokens",
                                        side_effect=exploding_estimate):
            with self.assertRaises(RuntimeError):
                self.mgr.replace_history(self.sid, compacted)
        # Old 5 messages still intact
        history = self.mgr.get_history(self.sid)
        self.assertEqual(len(history), 5)

if __name__ == "__main__":
    unittest.main()
