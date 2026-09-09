"""Regression tests for bounded search-provider response handling."""

import unittest
from unittest.mock import patch

from tools import websearch


class _StreamingResponse:
    status_code = 200

    def raise_for_status(self):
        return None

    @property
    def text(self):
        raise AssertionError("search response must not be materialized through response.text")

    def iter_content(self, chunk_size):
        yield b'<a class="result-link" href="https://example.com">Example</a>'

    def close(self):
        return None


class TestWebSearchResponseBounds(unittest.TestCase):
    def test_ddg_lite_streams_bounded_response_without_redirects(self):
        response = _StreamingResponse()
        with patch("tools.websearch.requests.post", return_value=response) as post:
            result = websearch._search_ddg_lite("example", 5, "", "")

        self.assertEqual(result["results"][0]["url"], "https://example.com")
        self.assertTrue(post.call_args.kwargs["stream"])
        self.assertFalse(post.call_args.kwargs["allow_redirects"])


if __name__ == "__main__":
    unittest.main()
