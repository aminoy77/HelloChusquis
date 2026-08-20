"""Regression tests for parameterized Monday GraphQL mutations."""

import unittest

from tools import monday


class TestMondayGraphqlSafety(unittest.TestCase):
    def test_create_board_uses_graphql_variable_payload(self):
        payload = monday._create_board_payload('name" ) { id } } mutation {')
        self.assertNotIn('name" )', payload["query"])
        self.assertEqual(payload["variables"], {"name": 'name" ) { id } } mutation {'})


if __name__ == "__main__":
    unittest.main()
