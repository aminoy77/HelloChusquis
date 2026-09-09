"""Regression tests for safe Facebook Graph API page identifiers."""

import unittest

from tools import facebook


class TestFacebookPageSafety(unittest.TestCase):
    def test_page_identifier_is_a_positive_numeric_path_segment(self):
        self.assertEqual(facebook._facebook_id("123456789012345"), "123456789012345")
        for unsafe_id in ("../me", "123/feed", "", "id\nX-Test: injected", "page_id"):
            with self.subTest(unsafe_id=unsafe_id):
                with self.assertRaises(ValueError):
                    facebook._facebook_id(unsafe_id)

    def test_page_and_message_text_are_bounded(self):
        self.assertEqual(facebook._bounded_text("Launch update", "message", 2000), "Launch update")
        for invalid_text in ("", "x" * 2001):
            with self.subTest(invalid_text=invalid_text[:10]):
                with self.assertRaises(ValueError):
                    facebook._bounded_text(invalid_text, "message", 2000)


if __name__ == "__main__":
    unittest.main()
