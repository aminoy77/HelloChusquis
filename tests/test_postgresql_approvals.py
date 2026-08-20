"""Regression tests for PostgreSQL side-effect approval classification."""

import unittest

from core.approvals import approval_reason


class TestPostgreSQLApprovals(unittest.TestCase):
    def test_execute_requires_approval(self):
        self.assertIsNotNone(approval_reason("postgresql", {"action": "execute", "sql": "DELETE FROM users"}))

    def test_query_with_mutating_statement_requires_approval(self):
        self.assertIsNotNone(approval_reason("postgresql", {"action": "query", "sql": "SELECT 1; DELETE FROM users"}))

    def test_single_select_remains_autonomous(self):
        self.assertIsNone(approval_reason("postgresql", {"action": "query", "sql": "SELECT id FROM users LIMIT 1"}))


if __name__ == "__main__":
    unittest.main()
