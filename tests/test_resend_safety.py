"""Regression tests for safe Resend outbound email payloads."""

import unittest

from tools import resend


class TestResendSafety(unittest.TestCase):
    def test_recipient_header_controls_are_rejected(self):
        with self.assertRaises(ValueError):
            resend._recipient("victim@example.com\r\nBcc: hidden@example.com")

    def test_batch_size_is_bounded(self):
        with self.assertRaises(ValueError):
            resend._bounded_batch([{}] * 101)


if __name__ == "__main__":
    unittest.main()
