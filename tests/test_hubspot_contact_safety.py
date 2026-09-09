"""Regression tests for safe HubSpot contact identifiers."""

import unittest

from tools import hubspot


class TestHubSpotContactSafety(unittest.TestCase):
    def test_contact_email_is_validated_and_encoded_as_one_path_segment(self):
        self.assertEqual(
            hubspot._contact_email_path_segment("person+tag@example.com"),
            "person%2Btag%40example.com",
        )
        for unsafe_email in ("person@example.com/../../deals", "person@example.com\nX-Test: injected", ""):
            with self.subTest(unsafe_email=unsafe_email):
                with self.assertRaises(ValueError):
                    hubspot._contact_email_path_segment(unsafe_email)


if __name__ == "__main__":
    unittest.main()
