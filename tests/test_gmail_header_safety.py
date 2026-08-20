"""Regression tests for Gmail message header injection protection."""

import unittest

from tools import gmail


class TestGmailHeaderSafety(unittest.TestCase):
    def test_encode_email_rejects_newlines_in_recipient_and_subject_headers(self):
        with self.assertRaises(ValueError):
            gmail.encode_email("sender@example.com", "victim@example.com\r\nBcc: hidden@example.com", "Subject", "Body")
        with self.assertRaises(ValueError):
            gmail.encode_email("sender@example.com", "victim@example.com", "Subject\nBcc: hidden@example.com", "Body")


if __name__ == "__main__":
    unittest.main()
