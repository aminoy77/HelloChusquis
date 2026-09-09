"""Regression tests for safe Instagram media identifiers."""

import unittest

from tools import instagram


class TestInstagramMediaSafety(unittest.TestCase):
    def test_media_identifier_is_a_positive_numeric_path_segment(self):
        self.assertEqual(instagram._instagram_id("17984519012345678"), "17984519012345678")
        for unsafe_id in ("../me", "1798/insights", "", "id\nX-Test: injected", "media_id"):
            with self.subTest(unsafe_id=unsafe_id):
                with self.assertRaises(ValueError):
                    instagram._instagram_id(unsafe_id)

    def test_media_url_and_page_limit_are_constrained(self):
        self.assertEqual(instagram._media_url("https://cdn.example.com/photo.jpg"), "https://cdn.example.com/photo.jpg")
        self.assertEqual(instagram._bounded_limit(999), 100)
        self.assertEqual(instagram._bounded_limit("invalid"), 10)
        for unsafe_url in ("http://cdn.example.com/photo.jpg", "https://user:pass@example.com/photo.jpg", ""):
            with self.subTest(unsafe_url=unsafe_url):
                with self.assertRaises(ValueError):
                    instagram._media_url(unsafe_url)


if __name__ == "__main__":
    unittest.main()
