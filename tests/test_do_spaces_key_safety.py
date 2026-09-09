"""Regression tests for safe DigitalOcean Spaces object key paths."""

import unittest

from tools import do_spaces


class TestDigitalOceanSpacesKeySafety(unittest.TestCase):
    def test_spaces_object_key_is_encoded_without_ambiguous_path_segments(self):
        self.assertEqual(do_spaces._spaces_key_path("reports/2026 final.csv"), "reports/2026%20final.csv")
        for unsafe_key in ("../secrets", "reports/../secrets", "", "report\nX-Test: injected"):
            with self.subTest(unsafe_key=unsafe_key):
                with self.assertRaises(ValueError):
                    do_spaces._spaces_key_path(unsafe_key)


if __name__ == "__main__":
    unittest.main()
