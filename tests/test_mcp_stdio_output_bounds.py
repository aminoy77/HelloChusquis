"""Regression tests for bounded MCP stdio diagnostic retention."""

import asyncio
import sys
import unittest

from core.mcp import StdioTransport


class TestMcpStdioOutputBounds(unittest.IsolatedAsyncioTestCase):
    async def test_stderr_retention_is_bounded_for_noisy_server(self):
        transport = StdioTransport(
            command=sys.executable,
            args=["-c", "import sys; [print(f'noise-{i}', file=sys.stderr) for i in range(250)]"],
        )
        await transport.connect()
        for _ in range(100):
            if transport._process and transport._process.poll() is not None:
                await asyncio.sleep(0.01)
                break
            await asyncio.sleep(0.01)
        await transport.close()

        self.assertLessEqual(len(transport._stderr_lines), 100)


if __name__ == "__main__":
    unittest.main()
