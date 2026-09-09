"""Regression tests for safe Asana task path identifiers."""

import unittest

from tools import asana


class TestAsanaPathSafety(unittest.TestCase):
    def test_task_identifier_rejects_path_injection(self):
        with self.assertRaises(ValueError):
            asana._task_id("task/../other")
        self.assertEqual(asana._task_id("1200000123456789"), "1200000123456789")


if __name__ == "__main__":
    unittest.main()
