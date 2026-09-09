"""Regression tests for Twilio account endpoint construction."""

import unittest

from tools import twilio


class TestTwilioAccountSid(unittest.TestCase):
    def test_account_sid_is_validated_and_interpolated(self):
        sid = "AC" + "a" * 32
        self.assertEqual(twilio._account_sid(sid), sid)
        with self.assertRaises(ValueError):
            twilio._account_sid("{account_sid}")


if __name__ == "__main__":
    unittest.main()
