"""Regression tests for safe Zendesk endpoint construction."""

import unittest

from tools import zendesk


class TestZendeskEndpointSafety(unittest.TestCase):
    def test_zendesk_subdomain_is_constrained_to_a_single_dns_label(self):
        self.assertEqual(
            zendesk._zendesk_base_url("support-team"),
            "https://support-team.zendesk.com/api/v2",
        )
        for unsafe_subdomain in ("support-team.zendesk.com", "support-team@127.0.0.1", "../admin", ""):
            with self.subTest(unsafe_subdomain=unsafe_subdomain):
                with self.assertRaises(ValueError):
                    zendesk._zendesk_base_url(unsafe_subdomain)


if __name__ == "__main__":
    unittest.main()
