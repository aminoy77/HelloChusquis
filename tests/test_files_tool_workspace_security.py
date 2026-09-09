"""Security regressions for FilesTool workspace enforcement."""

from pathlib import Path
import tempfile
import unittest

from tools.files import FilesTool


class TestFilesToolWorkspaceSecurity(unittest.TestCase):
    def test_home_directory_is_not_implicitly_authorized(self):
        with tempfile.TemporaryDirectory(dir=Path.home()) as outside_directory, tempfile.TemporaryDirectory() as workspace:
            outside_file = Path(outside_directory) / "secret.txt"
            outside_file.write_text("secret", encoding="utf-8")
            tool = FilesTool([workspace])

            result = tool.run("read", str(outside_file))

        self.assertFalse(result.success)
        self.assertIn("Access denied", result.error)

    def test_explicitly_granted_directory_remains_accessible(self):
        with tempfile.TemporaryDirectory() as workspace, tempfile.TemporaryDirectory() as granted_directory:
            allowed_file = Path(granted_directory) / "notes.txt"
            allowed_file.write_text("allowed", encoding="utf-8")
            tool = FilesTool([workspace])
            tool.allow_dir(granted_directory)

            result = tool.run("read", str(allowed_file))

        self.assertTrue(result.success)
        self.assertEqual(result.output, "allowed")


if __name__ == "__main__":
    unittest.main()
