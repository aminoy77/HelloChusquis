"""Audit #1: subagent nested dispatch must pass the same gates as run()."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from core.agent import Agent
from core.subagents import handle_subagent_tool
from tools.base import ToolResult


def _agent(deny=None, approval=None):
    agent = Agent.__new__(Agent)
    agent.tool_policy = SimpleNamespace(
        is_tool_allowed=lambda name: name not in (deny or ()),
    )
    agent.security_auditor = SimpleNamespace(audit_tool_call=lambda n, a: [])
    agent._authorization_denied_result = lambda n, a: None
    agent._approval_required_result = lambda n, a: approval
    agent._safe_dispatch = lambda n, a, approval_granted=False: ToolResult(
        success=True, output="DISPATCHED")
    agent.pool = object()
    agent.tools_schema = []
    return agent


class TestSubagentGates(unittest.TestCase):
    def test_gated_dispatch_denies_policy_blocked_tool(self):
        agent = _agent(deny=("slack",))
        result = agent._gated_dispatch("slack", {})
        self.assertFalse(result.success)
        self.assertIn("denied by policy", result.error)

    def test_gated_dispatch_blocks_on_approval_required(self):
        pending = ToolResult(success=False, output="", error="approval required")
        agent = _agent(approval=pending)
        result = agent._gated_dispatch("slack", {})
        self.assertEqual(result, pending)

    def test_gated_dispatch_passes_through_allowed_tool(self):
        agent = _agent()
        result = agent._gated_dispatch("web_search", {"query": "x"})
        self.assertTrue(result.success)
        self.assertEqual(result.output, "DISPATCHED")

    def test_subagent_run_uses_gated_dispatch(self):
        agent = _agent(deny=("slack",))
        with patch("core.subagents.run_one") as run_one:
            run_one.return_value = SimpleNamespace(
                ok=True, output="done", truncated=False, name="integrator")
            handle_subagent_tool(agent, {
                "action": "run", "name": "integrator", "task": "post"})
            dispatch_fn = run_one.call_args[0][2]
        self.assertEqual(dispatch_fn.__name__, "_gated_dispatch")

    def test_subagent_fanout_uses_gated_dispatch(self):
        agent = _agent()
        with patch("core.subagents.fanout") as fanout_fn:
            fanout_fn.return_value = [SimpleNamespace(
                ok=True, output="done", name="x")]
            handle_subagent_tool(agent, {
                "action": "fanout", "jobs": [{"name": "x", "task": "t"}]})
            dispatch_fn = fanout_fn.call_args[0][2]
        self.assertEqual(dispatch_fn.__name__, "_gated_dispatch")


if __name__ == "__main__":
    unittest.main()
