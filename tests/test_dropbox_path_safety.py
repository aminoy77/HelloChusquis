"""Regression tests for safe Dropbox paths."""

import unittest

from tools import dropbox


class TestDropboxPathSafety(unittest.TestCase):
    def test_dropbox_file_path_rejects_ambiguous_segments(self):
        self.assertEqual(dropbox._dropbox_path("/reports/2026 final.csv"), "/reports/2026 final.csv")
        for unsafe_path in ("reports/no-leading-slash", "/reports/../secrets", "/report\nX-Test: injected", "/"):
            with self.subTest(unsafe_path=unsafe_path):
                with self.assertRaises(ValueError):
                    dropbox._dropbox_path(unsafe_path)


if __name__ == "__main__":
    unittest.main()
