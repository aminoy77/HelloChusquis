"""Regression tests for safe Pipedrive deal filters."""

import unittest

from tools import pipedrive


class TestPipedriveFilterSafety(unittest.TestCase):
    def test_deal_status_is_constrained_to_supported_values(self):
        self.assertEqual(pipedrive._deal_status("OPEN"), "open")
        for unsafe_status in ("open&limit=1000", "../activities", "", "unknown"):
            with self.subTest(unsafe_status=unsafe_status):
                with self.assertRaises(ValueError):
                    pipedrive._deal_status(unsafe_status)


if __name__ == "__main__":
    unittest.main()
