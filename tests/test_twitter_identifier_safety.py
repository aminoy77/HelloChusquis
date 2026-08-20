"""Regression tests for safe Twitter API resource identifiers."""

import unittest

from tools import twitter


class TestTwitterIdentifierSafety(unittest.TestCase):
    def test_twitter_resource_identifier_is_a_positive_numeric_path_segment(self):
        self.assertEqual(twitter._twitter_id("1857350141375533158"), "1857350141375533158")
        for unsafe_id in ("../users", "123/tweets", "", "id\nX-Test: injected", "user_name"):
            with self.subTest(unsafe_id=unsafe_id):
                with self.assertRaises(ValueError):
                    twitter._twitter_id(unsafe_id)

    def test_query_and_post_inputs_are_bounded(self):
        self.assertEqual(twitter._bounded_max_results(999), 100)
        self.assertEqual(twitter._bounded_max_results("invalid"), 10)
        self.assertEqual(twitter._tweet_text("A concise update."), "A concise update.")
        for invalid_text in ("", "x" * 281):
            with self.subTest(invalid_text=invalid_text[:10]):
                with self.assertRaises(ValueError):
                    twitter._tweet_text(invalid_text)


if __name__ == "__main__":
    unittest.main()
