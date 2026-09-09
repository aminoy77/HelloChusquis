"""Regression tests for safe ActiveCampaign contact requests."""

import unittest

from tools import activecampaign


class TestActiveCampaignRequestSafety(unittest.TestCase):
    def test_contact_lookup_encodes_email_and_list_limit_is_bounded(self):
        self.assertEqual(activecampaign._contact_path("a/b@example.com"), "a%2Fb%40example.com")
        self.assertEqual(activecampaign._limit(-1), 1)
        self.assertEqual(activecampaign._limit(10000), 100)


if __name__ == "__main__":
    unittest.main()
