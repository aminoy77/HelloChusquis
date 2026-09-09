import asyncio
import unittest
from unittest.mock import AsyncMock, patch

import httpx

from tools import dropbox
from tools.new_integrations import GitHubActionsTool


class TestFeatureFixesRound2(unittest.TestCase):
    def test_github_actions_wrapper_delegates_to_real_integration(self):
        expected = {"workflows": [{"id": 42}]}
        with patch(
            "tools.github_actions.list_workflows",
            new=AsyncMock(return_value=expected),
        ) as list_workflows:
            result = GitHubActionsTool().run(
                "list_workflows",
                repository="owner/repo",
                token="secret",
            )

        self.assertTrue(result.success)
        self.assertEqual(result.output, str(expected))
        list_workflows.assert_awaited_once_with("owner/repo", "secret")

    def test_github_actions_wrapper_rejects_unknown_action(self):
        result = GitHubActionsTool().run("not_an_action", repository="owner/repo", token="secret")

        self.assertFalse(result.success)
        self.assertIn("Unknown action", result.error)

    def test_dropbox_json_request_raises_for_http_error(self):
        response = httpx.Response(401, request=httpx.Request("POST", "https://api.dropboxapi.com/2/test"))
        response.json = lambda: {"error": "unauthorized"}

        class _Client:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return False

            async def request(self, *args, **kwargs):
                return response

        with patch("tools.dropbox.httpx.AsyncClient", return_value=_Client()):
            with self.assertRaises(httpx.HTTPStatusError):
                asyncio.run(dropbox._json_request("POST", "https://api.dropboxapi.com/2/test", "secret"))


if __name__ == "__main__":
    unittest.main()
