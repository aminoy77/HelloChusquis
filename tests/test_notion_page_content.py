"""Regression tests for Notion page creation content handling."""

import asyncio
import unittest
from unittest.mock import patch

from tools import notion


class _Response:
    def raise_for_status(self):
        return None

    def json(self):
        return {"id": "page-id"}


class _AsyncClient:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.calls = []
        self.__class__.instances.append(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return None

    async def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return _Response()


class TestNotionPageContent(unittest.TestCase):
    def setUp(self):
        _AsyncClient.instances.clear()

    def test_create_page_preserves_text_content_as_paragraph_blocks(self):
        with patch("tools.notion.AsyncClient", _AsyncClient):
            asyncio.run(notion.create_page("secret", "0123456789abcdef0123456789abcdef", "Title", "First line\nSecond line"))

        client = _AsyncClient.instances[0]
        self.assertEqual(client.kwargs, {"timeout": 30, "follow_redirects": False})
        self.assertEqual(client.calls[0][0:2], ("POST", "https://api.notion.com/v1/pages"))
        payload = client.calls[0][2]["json"]
        self.assertEqual(
            payload["children"],
            [
                {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "First line"}}]}},
                {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Second line"}}]}},
            ],
        )


if __name__ == "__main__":
    unittest.main()
