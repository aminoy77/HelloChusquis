"""Regression tests for safe Jira API endpoint validation."""

import unittest

from tools import jira


class TestJiraEndpointSafety(unittest.TestCase):
    def test_jira_base_url_must_be_https_origin(self):
        self.assertEqual(jira._jira_base_url("https://team.atlassian.net/"), "https://team.atlassian.net")
        with self.assertRaises(ValueError):
            jira._jira_base_url("http://127.0.0.1:8080")
        with self.assertRaises(ValueError):
            jira._jira_base_url("https://team.atlassian.net/rest/api")


if __name__ == "__main__":
    unittest.main()
