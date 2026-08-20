"""Security regressions for MCP stdio process environments."""

import asyncio
import os
import sys
import unittest
from unittest.mock import patch

from core.mcp import StdioTransport


class TestMcpStdioEnvironment(unittest.IsolatedAsyncioTestCase):
    async def test_stdio_server_does_not_inherit_host_secrets(self):
        transport = StdioTransport(
            command=sys.executable,
            args=["-c", "import os; print(os.getenv('HELLOCHUSQUIS_TEST_SECRET', 'missing'))"],
        )
        environment = {**os.environ, "HELLOCHUSQUIS_TEST_SECRET": "do-not-leak"}

        with patch.dict(os.environ, environment, clear=True):
            await transport.connect()
            line = await asyncio.get_running_loop().run_in_executor(
                None, transport._process.stdout.readline
            )
            await transport.close()

        self.assertEqual(line.decode("utf-8").strip(), "missing")


if __name__ == "__main__":
    unittest.main()
