"""Unit tests for the agent-level human approval gate."""

from __future__ import annotations

import unittest

from core.agent import Agent
from core.approvals import ApprovalManager
from tools.base import ToolResult


class _AuditSink:
    def log_audit_event(self, session_id, event_type, details):
        return 1


class TestAgentApprovalGate(unittest.TestCase):
    def _agent(self, require_approval=True):
        agent = Agent.__new__(Agent)
        agent.require_approval = require_approval
        agent.approval_manager = ApprovalManager()
        agent._audited_approval_ids = set()
        agent._session_id = "test-session"
        agent.session_manager = _AuditSink()
        return agent

    def test_high_impact_call_is_blocked_before_dispatch(self):
        agent = self._agent()

        result = agent._approval_required_result("shell", {"command": "echo hello"})

        self.assertFalse(result.success)
        self.assertIn("Approval required: apr_", result.error)
        self.assertEqual(len(agent.pending_approvals()), 1)

    def test_read_only_call_remains_autonomous(self):
        agent = self._agent()

        result = agent._approval_required_result(
            "files", {"action": "read", "path": "/tmp/notes.txt"}
        )

        self.assertIsNone(result)
        self.assertEqual(agent.pending_approvals(), [])

    def test_approved_action_dispatches_once(self):
        agent = self._agent()
        blocked = agent._approval_required_result("files", {"action": "delete", "path": "/tmp/a"})
        request_id = blocked.error.split("Approval required: ", 1)[1].split(".", 1)[0]
        calls = []

        def dispatch(name, args, approval_granted=False):
            calls.append((name, args, approval_granted))
            return ToolResult(success=True, output="deleted")

        agent._dispatch_tool = dispatch
        agent.decide_approval(request_id, approved=True)
        result = agent.execute_approved(request_id)

        self.assertTrue(result.success)
        self.assertEqual(
            calls,
            [("files", {"action": "delete", "path": "/tmp/a"}, True)],
        )
        with self.assertRaises(ValueError):
            agent.execute_approved(request_id)

    def test_approved_action_is_rechecked_against_current_policy(self):
        agent = self._agent()
        blocked = agent._approval_required_result("files", {"action": "delete", "path": "/tmp/a"})
        request_id = blocked.error.split("Approval required: ", 1)[1].split(".", 1)[0]
        agent.tool_policy = type("Policy", (), {"is_tool_allowed": lambda _self, _tool: False})()

        def dispatch(*_args, **_kwargs):
            self.fail("A policy-revoked approval must not dispatch a tool")

        agent._dispatch_tool = dispatch
        agent.decide_approval(request_id, approved=True)
        result = agent.execute_approved(request_id)

        self.assertFalse(result.success)
        self.assertEqual(result.error, "Tool execution denied by current policy.")
        with self.assertRaises(ValueError):
            agent.execute_approved(request_id)

    def test_plugin_exception_does_not_expose_sensitive_detail(self):
        agent = self._agent(require_approval=False)
        agent._external_tool_modules = {}

        def fail(**_kwargs):
            raise RuntimeError("provider token=super-secret")

        agent.plugins = [{"name": "failing-plugin", "run": fail}]
        result = agent._dispatch_tool("failing-plugin", {})

        self.assertFalse(result.success)
        self.assertEqual(result.error, "failing-plugin tool failed. Check server logs.")
        self.assertNotIn("super-secret", result.error)


if __name__ == "__main__":
    unittest.main()
