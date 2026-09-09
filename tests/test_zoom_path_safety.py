"""Regression tests for safe Zoom meeting path identifiers."""

import unittest

from tools import zoom


class TestZoomPathSafety(unittest.TestCase):
    def test_meeting_identifier_rejects_path_injection(self):
        with self.assertRaises(ValueError):
            zoom._meeting_id("meeting/../recordings")
        self.assertEqual(zoom._meeting_id("1234567890"), "1234567890")


if __name__ == "__main__":
    unittest.main()
