"""Regression tests for streaming, bounded web response reading."""

import unittest
from unittest.mock import patch

from tools.web_fetch import WebFetchTool


class _StreamingResponse:
    status_code = 200
    headers = {"content-type": "text/markdown"}
    url = "https://example.com/article"

    def __init__(self):
        self.closed = False

    @property
    def content(self):
        raise AssertionError("response.content must not be materialized for bounded fetches")

    def iter_content(self, chunk_size):
        yield b"# heading\n"
        yield b"bounded response"

    def close(self):
        self.closed = True


class TestWebFetchStreamingBounds(unittest.TestCase):
    def test_fetch_streams_body_without_materializing_response_content(self):
        tool = WebFetchTool(max_response_bytes=64_000)
        response = _StreamingResponse()

        with patch("tools.web_fetch.requests.get", return_value=response) as get:
            result = tool._fetch_and_extract("https://example.com/article", "markdown", 1_000)

        self.assertEqual(result["text"].split("\n\n", 1)[-1], "# heading\nbounded response")
        self.assertTrue(get.call_args.kwargs["stream"])
        self.assertTrue(response.closed)


if __name__ == "__main__":
    unittest.main()
