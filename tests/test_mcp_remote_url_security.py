"""Security regressions for remote MCP transport endpoints."""

import unittest

from core.mcp import HTTPTransport, SSETransport


class TestMcpRemoteUrlSecurity(unittest.TestCase):
    def test_remote_transports_reject_unsafe_urls_at_construction(self):
        for transport in (HTTPTransport, SSETransport):
            for url in (
                "http://example.com/mcp",
                "https://127.0.0.1/mcp",
                "https://token@example.com/mcp",
            ):
                with self.assertRaises(ValueError):
                    transport(url)


if __name__ == "__main__":
    unittest.main()
