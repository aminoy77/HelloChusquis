"""Regression: MCP connect must not crash or poison the connected flag."""

import unittest

from core.agent import Agent


class _FailingClient:
    def connect(self):
        raise RuntimeError("mcp server unreachable")


class TestAgentMcpConnect(unittest.TestCase):
    def test_failed_connect_keeps_flag_unset(self):
        agent = object.__new__(Agent)
        agent.mcp_client = _FailingClient()

        agent._ensure_mcp_connected()

        self.assertFalse(getattr(agent, "_mcp_connected", False))


if __name__ == "__main__":
    unittest.main()
