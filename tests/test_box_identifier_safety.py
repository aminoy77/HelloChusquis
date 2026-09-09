"""Regression tests for safe Box file and folder identifiers."""

import unittest

from tools import box


class TestBoxIdentifierSafety(unittest.TestCase):
    def test_box_identifier_is_a_positive_numeric_path_segment(self):
        self.assertEqual(box._box_id("1234567890", "file_id"), "1234567890")
        for unsafe_id in ("../folders", "file/content", "", "id\nX-Test: injected"):
            with self.subTest(unsafe_id=unsafe_id):
                with self.assertRaises(ValueError):
                    box._box_id(unsafe_id, "file_id")


if __name__ == "__main__":
    unittest.main()
