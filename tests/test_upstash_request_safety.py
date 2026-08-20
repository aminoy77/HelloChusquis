"""Regression tests for Upstash mutation approvals and safe Redis REST paths."""

import unittest

from core.approvals import approval_reason
from tools import upstash


class TestUpstashRequestSafety(unittest.TestCase):
    def test_increment_and_delete_require_approval(self):
        self.assertIsNotNone(approval_reason("upstash", {"action": "incr", "key": "counter"}))
        self.assertIsNotNone(approval_reason("upstash", {"action": "del", "key": "session"}))

    def test_keys_are_encoded_as_single_path_segments(self):
        self.assertEqual(upstash._key_path("a/b?c"), "a%2Fb%3Fc")


if __name__ == "__main__":
    unittest.main()
