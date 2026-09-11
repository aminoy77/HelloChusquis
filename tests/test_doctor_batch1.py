"""Doctor batch1: duplicates, workspace, KB stats, ports, browser readiness."""
import unittest
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.setup import (
    find_duplicate_providers,
    check_workspace_dirs,
    count_kb_files,
    check_ports_free,
    check_browser_ready,
)


class TestDuplicates(unittest.TestCase):
    def test_flags_same_name_twice(self):
        providers = [
            {"name": "Ollama (local)", "base_url": "http://localhost:11434/v1"},
            {"name": "groq", "base_url": "https://api.groq.com/openai/v1"},
            {"name": "Ollama (local)", "base_url": "http://localhost:11434/v1"},
        ]
        self.assertEqual(find_duplicate_providers(providers), ["Ollama (local)"])

    def test_no_false_positive(self):
        providers = [
            {"name": "Ollama (local)-3", "base_url": "x"},
            {"name": "Ollama (local)-4", "base_url": "x"},
        ]
        self.assertEqual(find_duplicate_providers(providers), [])


class TestWorkspace(unittest.TestCase):
    def test_missing_dir_reported(self):
        missing = check_workspace_dirs(["/nonexistent-xyz-123"])
        self.assertEqual(len(missing), 1)
        self.assertFalse(missing[0][1])

    def test_existing_dir_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(check_workspace_dirs([tmp])[0][1])


class TestKbCount(unittest.TestCase):
    def test_counts_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "a.md").write_text("# hi")
            Path(tmp, "sub").mkdir()
            Path(tmp, "sub", "b.md").write_text("# yo")
            Path(tmp, "c.txt").write_text("nope")
            self.assertEqual(count_kb_files(Path(tmp)), 2)


class TestPorts(unittest.TestCase):
    def test_loopback_free_port_reports_free(self):
        import socket
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        free = s.getsockname()[1]
        s.close()
        self.assertTrue(check_ports_free([free])[free])

    def test_occupied_port_reports_busy(self):
        import socket
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        try:
            self.assertFalse(check_ports_free([s.getsockname()[1]])[s.getsockname()[1]])
        finally:
            s.close()


class TestBrowserReady(unittest.TestCase):
    def test_missing_dir_means_not_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            ok, hint = check_browser_ready(Path(tmp) / "nope")
            self.assertFalse(ok)
            self.assertIn("playwright install", hint)


if __name__ == "__main__":
    unittest.main()
