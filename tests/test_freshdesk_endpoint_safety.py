"""Regression tests for safe Freshdesk endpoint construction."""

import unittest

from tools import freshdesk


class TestFreshdeskEndpointSafety(unittest.TestCase):
    def test_freshdesk_account_is_constrained_to_a_single_dns_label(self):
        self.assertEqual(
            freshdesk._freshdesk_base_url("support-team"),
            "https://support-team.freshdesk.com/api/v2",
        )
        for unsafe_account in ("support-team.freshdesk.com", "support-team@127.0.0.1", "../admin", ""):
            with self.subTest(unsafe_account=unsafe_account):
                with self.assertRaises(ValueError):
                    freshdesk._freshdesk_base_url(unsafe_account)

    def test_ticket_identifiers_and_filters_are_constrained(self):
        self.assertEqual(freshdesk._ticket_id("12345"), "12345")
        self.assertEqual(freshdesk._ticket_filter("PENDING"), "pending")
        for unsafe_id in ("../tickets", "123/reply", "", "id\nX-Test: injected"):
            with self.subTest(unsafe_id=unsafe_id):
                with self.assertRaises(ValueError):
                    freshdesk._ticket_id(unsafe_id)
        with self.assertRaises(ValueError):
            freshdesk._ticket_filter("open&include=admin")


if __name__ == "__main__":
    unittest.main()
