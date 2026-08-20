"""Regression tests for safe PagerDuty incident API paths."""

import unittest

from tools import pagerduty


class TestPagerDutyPathSafety(unittest.TestCase):
    def test_incident_identifier_rejects_path_injection(self):
        with self.assertRaises(ValueError):
            pagerduty._incident_id("incident/../other")
        self.assertEqual(pagerduty._incident_id("PABC123"), "PABC123")


if __name__ == "__main__":
    unittest.main()
