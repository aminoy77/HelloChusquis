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
        now = [1000.0]
        rl = RateLimiter(requests_per_minute=10, clock=lambda: now[0])
        try:
            rl.is_allowed("active")
            now[0] += 70.0
            rl.is_allowed("newcomer")
            rl._cleanup()
            # Fully-expired client evicted, active window kept.
            self.assertNotIn("active", rl._hits)
            self.assertIn("newcomer", rl._hits)
        finally:
            rl.close()

    def test_web_concurrency_and_limits(self):
        import web.server as srv
        # Upstream uses per-session turn locks + request-local callback,
        # not a shared-dispatcher monkey-patch.
        src = Path("web/server.py").read_text()
        self.assertIn("try_acquire_turn", src)
        self.assertIn("tool_result_callback", src)
        self.assertIn("release_turn", src)
        self.assertEqual(srv._feedback_limiter._limit, 10)
        # /status must use the shared db_memory store, not a raw per-request
        # sqlite3 connection (the old one leaked a connection per call).
        self.assertNotIn("sqlite3.connect", src)
        self.assertIn("get_session_count", src)

    def test_cli_flag_guard(self):
        src = Path("cli.py").read_text()
        self.assertIn("args.quick and args.command is None", src)
        self.assertIn("args.show and args.command is None", src)


if __name__ == "__main__":
    unittest.main()
