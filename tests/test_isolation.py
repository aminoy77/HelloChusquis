"""Regression: workspace/files isolation + rate limiter prune + web/cli."""
import tempfile
import threading
import time
import unittest
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.files import FilesTool
from workspace.manager import WorkspaceManager
from core.rate_limiter import RateLimiter


class TestIsolation(unittest.TestCase):
    def test_home_not_allowed_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(FilesTool([tmp])._is_allowed(Path.home() / ".ssh/id_rsa"))
            self.assertFalse(WorkspaceManager([tmp]).is_allowed(str(Path.home() / ".ssh/id_rsa")))
            self.assertTrue(FilesTool([tmp])._is_allowed(Path(tmp) / "a.txt"))

    def test_cleanup_prunes_stale(self):
        rl = RateLimiter(requests_per_minute=10)
        now = time.time()
        rl._hits["m"] = [now - 70, now]
        rl._cleanup()
        self.assertEqual(len(rl._hits["m"]), 1)
        rl._hits["old"] = [now - 70]
        rl._cleanup()
        self.assertNotIn("old", rl._hits)

    def test_web_concurrency_and_limits(self):
        import web.server as srv
        self.assertIsInstance(srv._chat_lock, type(threading.Lock()))
        self.assertEqual(srv._feedback_limiter._limit, 10)
        src = Path("web/server.py").read_text()
        self.assertIn("with _chat_lock", src)
        self.assertIn("with sqlite3.connect", src)

    def test_cli_flag_guard(self):
        src = Path("cli.py").read_text()
        self.assertIn("args.quick and args.command is None", src)
        self.assertIn("args.show and args.command is None", src)


if __name__ == "__main__":
    unittest.main()
