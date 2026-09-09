"""Regression tests for ClickUp task path identifiers."""

import unittest

from tools import clickup


class TestClickUpPathSafety(unittest.TestCase):
    def test_task_identifier_rejects_path_injection(self):
        with self.assertRaises(ValueError):
            clickup._resource_id("task/../other", "task")
        self.assertEqual(clickup._resource_id("abc_123", "task"), "abc_123")


if __name__ == "__main__":
    unittest.main()
