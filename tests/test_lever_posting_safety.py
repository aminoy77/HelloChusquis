"""Regression tests for safe Lever posting identifiers."""

import unittest

from tools import lever


class TestLeverPostingSafety(unittest.TestCase):
    def test_lever_posting_identifier_is_a_single_safe_path_segment(self):
        self.assertEqual(lever._posting_id("abc123_DEF-09"), "abc123_DEF-09")
        for unsafe_id in ("../stages", "posting/other", "", "id\nX-Test: injected"):
            with self.subTest(unsafe_id=unsafe_id):
                with self.assertRaises(ValueError):
                    lever._posting_id(unsafe_id)


if __name__ == "__main__":
    unittest.main()
