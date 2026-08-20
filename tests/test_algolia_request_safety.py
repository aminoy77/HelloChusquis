"""Regression tests for Algolia approvals and endpoint construction."""

import unittest

from core.approvals import approval_reason
from tools import algolia


class TestAlgoliaRequestSafety(unittest.TestCase):
    def test_add_object_requires_approval(self):
        self.assertIsNotNone(approval_reason("algolia", {"action": "add_object", "data": {"title": "record"}}))

    def test_application_identifier_cannot_escape_the_algolia_host(self):
        with self.assertRaises(ValueError):
            algolia._app_id("good/evil")
        self.assertEqual(algolia._app_id("ABC123"), "ABC123")


if __name__ == "__main__":
    unittest.main()
