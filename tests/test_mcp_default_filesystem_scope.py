"""Regression tests for private default MCP filesystem scope."""

from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

from core import mcp


class TestMcpDefaultFilesystemScope(unittest.TestCase):
    def test_default_filesystem_workspace_is_private_and_not_shared_tmp(self):
        with tempfile.TemporaryDirectory() as directory:
            root = mcp._ensure_default_filesystem_workspace(Path(directory) / "mcp-files")

            self.assertNotEqual(str(root), "/tmp")
            self.assertEqual(stat.S_IMODE(root.stat().st_mode), 0o700)

    def test_default_filesystem_server_receives_private_workspace(self):
        private_root = Path("/safe/private/mcp-files")
        with patch("core.mcp._ensure_default_filesystem_workspace", return_value=private_root):
            configs = mcp.build_default_configs()

        self.assertEqual(configs["filesystem"].args[-1], str(private_root))


if __name__ == "__main__":
    unittest.main()
