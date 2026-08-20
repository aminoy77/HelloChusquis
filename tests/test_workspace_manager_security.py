"""Security regressions for workspace authorization."""

from pathlib import Path
import tempfile
import unittest

from workspace.manager import WorkspaceManager


class TestWorkspaceManagerSecurity(unittest.TestCase):
    def test_home_directory_is_not_implicitly_allowed(self):
        with tempfile.TemporaryDirectory(dir=Path.home()) as outside_directory, tempfile.TemporaryDirectory() as workspace:
            manager = WorkspaceManager([workspace])

            self.assertFalse(manager.is_allowed(outside_directory))


if __name__ == "__main__":
    unittest.main()
