"""Regression tests for deterministic Mailchimp subscriber identifiers."""

import unittest

from tools import mailchimp


class TestMailchimpSubscriberHash(unittest.TestCase):
    def test_subscriber_hash_uses_lowercase_email_md5(self):
        self.assertEqual(
            mailchimp._subscriber_hash("USER@Example.COM"),
            "b58996c504c5638798eb6b511e6f49af",
        )


if __name__ == "__main__":
    unittest.main()
