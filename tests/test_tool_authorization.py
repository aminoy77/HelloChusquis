"""Authorization is enforced at tool dispatch, not only at HTTP routes."""

from __future__ import annotations

import unittest

from core.agent import Agent
from core.approvals import ApprovalManager
from core.identity import Role
from tools.base import ToolResult


class _AuditSink:
    def __init__(self):
        self.events = []

    def log_audit_event(self, session_id, event_type, details):
        self.events.append((event_type, details))
        return len(self.events)


class TestToolAuthorization(unittest.TestCase):
    def _agent(self, role):
        agent = Agent.__new__(Agent)
        agent.require_approval = True
        agent.role = role
        agent.approval_manager = ApprovalManager()
        agent._audited_approval_ids = set()
        agent._session_id = "test-session"
        agent.session_manager = _AuditSink()
        return agent

    def test_viewer_cannot_reach_a_mutating_tool_even_through_the_model(self):
        agent = self._agent(Role.VIEWER)

        result = agent._authorization_denied_result("shell", {"command": "rm -rf /"})

        self.assertFalse(result.success)
        self.assertIn("Not authorized", result.error)
        self.assertEqual(agent.pending_approvals(), [])
        self.assertEqual(agent.session_manager.events[0][0], "authorization_denied")

    def test_viewer_may_still_use_read_only_tools(self):
        agent = self._agent(Role.VIEWER)

        self.assertIsNone(
            agent._authorization_denied_result("files", {"action": "read", "path": "/tmp/a"})
        )

    def test_operator_reaches_the_approval_gate_instead_of_a_denial(self):
        agent = self._agent(Role.OPERATOR)

        self.assertIsNone(agent._authorization_denied_result("shell", {"command": "ls"}))
        blocked = agent._approval_required_result("shell", {"command": "ls"})
        self.assertIn("Approval required: apr_", blocked.error)

    def test_agents_without_a_role_are_unrestricted(self):
        agent = self._agent(None)

        self.assertIsNone(agent._authorization_denied_result("shell", {"command": "ls"}))

    def test_approved_action_is_re_checked_before_execution(self):
        agent = self._agent(Role.OPERATOR)
        blocked = agent._approval_required_result("files", {"action": "delete", "path": "/tmp/a"})
        request_id = blocked.error.split("Approval required: ", 1)[1].split(".", 1)[0]
        agent.decide_approval(request_id, approved=True)
        dispatched = []

        def dispatch(name, args, approval_granted=False):
            dispatched.append(name)
            return ToolResult(success=True, output="done")

        agent._dispatch_tool = dispatch
        agent.role = Role.VIEWER  # demoted after the approval was granted

        result = agent.execute_approved(request_id)

        self.assertFalse(result.success)
        self.assertIn("Not authorized", result.error)
        self.assertEqual(dispatched, [])


if __name__ == "__main__":
    unittest.main()
