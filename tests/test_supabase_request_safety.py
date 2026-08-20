"""Regression tests for Supabase mutation approval and endpoint safety."""

import unittest

from core.approvals import approval_reason
from tools import supabase


class TestSupabaseRequestSafety(unittest.TestCase):
    def test_run_sql_requires_approval(self):
        self.assertIsNotNone(approval_reason("supabase", {"action": "run_sql", "sql": "DROP TABLE users"}))

    def test_project_reference_cannot_escape_the_supabase_subdomain(self):
        with self.assertRaises(ValueError):
            supabase._project_ref("evil.example/")
        self.assertEqual(supabase._project_ref("abcdefghijklmnopqrst"), "abcdefghijklmnopqrst")


if __name__ == "__main__":
    unittest.main()
