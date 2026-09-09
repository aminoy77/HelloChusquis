"""Regression tests for safe GitHub Actions repository routes."""

import unittest

from tools import github_actions


class TestGitHubActionsRepositorySafety(unittest.TestCase):
    def test_repository_is_a_safe_owner_repository_pair(self):
        self.assertEqual(github_actions._repository("aminoy77/HelloChusquis"), "aminoy77/HelloChusquis")
        for unsafe_repository in ("aminoy77/../admin", "owner/repo/actions", "owner", "owner/repo\nX-Test: injected"):
            with self.subTest(unsafe_repository=unsafe_repository):
                with self.assertRaises(ValueError):
                    github_actions._repository(unsafe_repository)


if __name__ == "__main__":
    unittest.main()
