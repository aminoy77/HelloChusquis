"""Regression tests for complete conversation deletion."""

import unittest

from core.agent import Agent
from core.approvals import ApprovalManager


class _History:
    def __init__(self):
        self.cleared = False

    def clear(self):
        self.cleared = True


class _SessionManager:
    def __init__(self):
        self.cleared_ids = []

    def clear_history(self, session_id):
        self.cleared_ids.append(session_id)


class TestAgentClearConversation(unittest.TestCase):
    def test_clear_removes_persistent_history_and_cancels_pending_approval(self):
        agent = Agent.__new__(Agent)
        agent.history = _History()
        agent.session_manager = _SessionManager()
        agent._session_id = "persisted-session"
        agent._pending_tool_results = [{"role": "tool", "content": "stale"}]
        agent.approval_manager = ApprovalManager()
        pending = agent.approval_manager.request_for(
            "files", {"action": "delete", "path": "/tmp/example"}
        )

        result = agent.clear_conversation()

        self.assertTrue(agent.history.cleared)
        self.assertEqual(agent.session_manager.cleared_ids, ["persisted-session"])
        self.assertEqual(agent._pending_tool_results, [])
        self.assertEqual(result, {"cancelled_approvals": 1})
        with self.assertRaises(ValueError):
            agent.approval_manager.decide(pending.id, approved=True)


if __name__ == "__main__":
    unittest.main()
