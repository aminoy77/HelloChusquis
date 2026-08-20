"""Regression tests for safe Google Drive resource identifiers."""

import unittest

from tools import google_drive


class TestGoogleDriveIdentifierSafety(unittest.TestCase):
    def test_drive_identifier_is_constrained_to_one_safe_path_segment(self):
        self.assertEqual(google_drive._drive_id("1AbC_def-09"), "1AbC_def-09")
        for unsafe_id in ("../permissions", "file/permissions", "", "id\nX-Test: injected"):
            with self.subTest(unsafe_id=unsafe_id):
                with self.assertRaises(ValueError):
                    google_drive._drive_id(unsafe_id)

    def test_drive_inputs_are_bounded_and_control_characters_rejected(self):
        self.assertEqual(google_drive._bounded_page_size(9999), 1000)
        self.assertEqual(google_drive._bounded_page_size("invalid"), 100)
        self.assertEqual(google_drive._file_name("report.txt"), "report.txt")
        for invalid_name in ("", "report\n.txt"):
            with self.subTest(invalid_name=invalid_name):
                with self.assertRaises(ValueError):
                    google_drive._file_name(invalid_name)
        with self.assertRaises(ValueError):
            google_drive._email("recipient@example.com\nX-Test: injected")


if __name__ == "__main__":
    unittest.main()
