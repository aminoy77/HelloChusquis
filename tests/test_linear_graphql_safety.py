"""Regression tests for parameterized Linear GraphQL mutations."""

import unittest

from tools import linear


class TestLinearGraphqlSafety(unittest.TestCase):
    def test_workspace_payload_uses_valid_mutation_and_variables(self):
        payload = linear._create_workspace_payload('name" ) { id } } mutation {')
        self.assertTrue(payload["query"].startswith("mutation"))
        self.assertNotIn('name" )', payload["query"])
        self.assertEqual(payload["variables"], {"name": 'name" ) { id } } mutation {'})


if __name__ == "__main__":
    unittest.main()
