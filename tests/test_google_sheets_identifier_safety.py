"""Regression tests for safe Google Sheets resource identifiers."""

import unittest

from tools import google_sheets


class TestGoogleSheetsIdentifierSafety(unittest.TestCase):
    def test_spreadsheet_identifier_is_constrained_to_one_safe_path_segment(self):
        self.assertEqual(google_sheets._spreadsheet_id("1AbC_def-09"), "1AbC_def-09")
        for unsafe_id in ("../drive", "sheet/values", "", "id\nX-Test: injected"):
            with self.subTest(unsafe_id=unsafe_id):
                with self.assertRaises(ValueError):
                    google_sheets._spreadsheet_id(unsafe_id)

    def test_ranges_are_encoded_and_write_values_are_validated(self):
        self.assertEqual(google_sheets._range_path("Quarterly report!A1:B2"), "Quarterly%20report%21A1%3AB2")
        self.assertEqual(google_sheets._values([["safe", 1]]), [["safe", 1]])
        for invalid_range in ("", "Sheet1!A1\nX-Test: injected"):
            with self.subTest(invalid_range=invalid_range):
                with self.assertRaises(ValueError):
                    google_sheets._range_path(invalid_range)
        for invalid_values in ([], ["not-a-row"]):
            with self.subTest(invalid_values=invalid_values):
                with self.assertRaises(ValueError):
                    google_sheets._values(invalid_values)


if __name__ == "__main__":
    unittest.main()
