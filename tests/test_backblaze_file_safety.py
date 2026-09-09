"""Regression tests for safe Backblaze B2 file identifiers."""

import unittest

from tools import backblaze


class TestBackblazeFileSafety(unittest.TestCase):
    def test_b2_file_identifier_is_a_single_safe_token(self):
        self.assertEqual(backblaze._file_id("4_z123abc_456def"), "4_z123abc_456def")
        for unsafe_id in ("file&other=value", "../buckets", "", "id\nX-Test: injected"):
            with self.subTest(unsafe_id=unsafe_id):
                with self.assertRaises(ValueError):
                    backblaze._file_id(unsafe_id)


if __name__ == "__main__":
    unittest.main()
