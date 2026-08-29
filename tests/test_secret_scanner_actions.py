"""Regression tests for the secret scanner entry point."""

import os
import tempfile
import unittest

from tools import secret_scanner


class TestSecretScannerActions(unittest.TestCase):
    def test_check_env_reports_matches_without_unbound_local_error(self):
        with tempfile.TemporaryDirectory() as workdir:
            os.environ["HELLOCHUSQUIS_TEST_SECRET"] = "AKIA" + "A" * 16
            try:
                result = secret_scanner.run("check_env", path=workdir)
            finally:
                os.environ.pop("HELLOCHUSQUIS_TEST_SECRET", None)
        self.assertNotIn("Error:", result)
        self.assertIn("HELLOCHUSQUIS_TEST_SECRET", result)

    def test_missing_path_is_reported(self):
        self.assertEqual(secret_scanner.run("scan"), "Error: path required")
        self.assertIn("Path not found", secret_scanner.run("scan", path="/nonexistent/hellochusquis"))


if __name__ == "__main__":
    unittest.main()
