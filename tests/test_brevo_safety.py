"""Regression tests for bounded, safe Brevo contact payloads."""

import unittest

from tools import brevo


class TestBrevoSafety(unittest.TestCase):
    def test_recipient_controls_are_rejected(self):
        with self.assertRaises(ValueError):
            brevo._email("victim@example.com\r\nBcc: hidden@example.com")

    def test_contact_import_is_bounded(self):
        with self.assertRaises(ValueError):
            brevo._contacts([{}] * 1_001)


if __name__ == "__main__":
    unittest.main()
