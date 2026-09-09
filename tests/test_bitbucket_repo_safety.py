"""Regression tests for safe Bitbucket repository identifiers."""

import unittest

from tools import bitbucket


class TestBitbucketRepositorySafety(unittest.TestCase):
    def test_repository_identifier_is_a_single_safe_path_segment(self):
        self.assertEqual(bitbucket._repo_slug("hello-chusquis_1"), "hello-chusquis_1")
        for unsafe_repo in ("../workspace", "repo/pullrequests", "", "repo\nX-Test: injected"):
            with self.subTest(unsafe_repo=unsafe_repo):
                with self.assertRaises(ValueError):
                    bitbucket._repo_slug(unsafe_repo)


if __name__ == "__main__":
    unittest.main()
