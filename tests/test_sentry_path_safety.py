"""Regression tests for safe Sentry API path identifiers."""

import unittest

from tools import sentry


class TestSentryPathSafety(unittest.TestCase):
    def test_path_identifier_rejects_path_and_query_injection(self):
        with self.assertRaises(ValueError):
            sentry._path_id("issue/../other?x=1", "issue")
        self.assertEqual(sentry._path_id("12345", "issue"), "12345")


if __name__ == "__main__":
    unittest.main()
