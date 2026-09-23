"""Security regressions for workspace authorization."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from workspace.manager import WorkspaceManager


class TestWorkspaceManagerSecurity(unittest.TestCase):
    def test_home_directory_is_not_implicitly_allowed(self):
        with tempfile.TemporaryDirectory(dir=Path.home()) as outside_directory, tempfile.TemporaryDirectory() as workspace:
            manager = WorkspaceManager([workspace])

            self.assertFalse(manager.is_allowed(outside_directory))

    def test_headless_request_access_denies_without_prompt(self):
        with tempfile.TemporaryDirectory() as workspace:
            manager = WorkspaceManager([workspace])
            outside = str(Path(workspace).parent / "nope.txt")
            with patch.object(sys.stdin, "isatty", return_value=False):
                self.assertFalse(manager.request_access(outside))

    def test_eof_on_prompt_denies(self):
        with tempfile.TemporaryDirectory() as workspace:
            manager = WorkspaceManager([workspace])
            outside = str(Path(workspace).parent / "nope.txt")
            with patch.object(sys.stdin, "isatty", return_value=True), \
                 patch("workspace.manager.Confirm.ask", side_effect=EOFError):
                self.assertFalse(manager.request_access(outside))


if __name__ == "__main__":
    unittest.main()
