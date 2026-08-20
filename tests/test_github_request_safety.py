"""Regression tests for safe GitHub integration defaults and transport."""

import os
import unittest
from unittest.mock import patch

from tools import github


class _Response:
    def raise_for_status(self):
        return None

    def json(self):
        return {"name": "safe-repository"}


class _Client:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.calls = []
        self.closed = False
        self.__class__.instances.append(self)

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return _Response()

    def close(self):
        self.closed = True


class TestGitHubRequestSafety(unittest.TestCase):
    def setUp(self):
        _Client.instances.clear()

    @patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_test"}, clear=False)
    @patch("tools.github.httpx.Client", _Client)
    def test_repository_creation_is_private_by_default_and_closes_client(self):
        result = github._run_sync("create_repo", "ghp_test", {"name": "safe-repository"})

        client = _Client.instances[0]
        self.assertIn("safe-repository", result)
        self.assertEqual(client.kwargs, {"timeout": 30, "follow_redirects": False})
        self.assertTrue(client.calls[0][1]["json"]["private"])
        self.assertTrue(client.closed)


if __name__ == "__main__":
    unittest.main()
