"""Persistent approval audit trail regression tests."""

from pathlib import Path
import tempfile
import unittest

from api import main as api_main
from core.agent import Agent
from core.approvals import ApprovalManager
from core.history import History
from core.session import SessionManager
from tools.base import ToolResult
from types import SimpleNamespace
from unittest.mock import patch
from web import server as web_server


class _AuditSessionManager:
    def __init__(self):
        self.events = []

    def log_audit_event(self, session_id, event_type, details):
        self.events.append((session_id, event_type, details))


class TestSessionAuditPersistence(unittest.TestCase):
    def test_events_survive_reopening_a_stable_session_and_are_deleted_with_it(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "sessions.db"
            first = SessionManager(db_path)
            session_id = first.create_session("http", session_id="stable-session")
            first.log_audit_event(session_id, "approval_requested", {"approval_id": "apr_1"})
            first.close()

            reopened = SessionManager(db_path)
            reopened.create_session("http", session_id="stable-session")
            events = reopened.list_audit_events("stable-session")
            self.assertEqual(events[0]["event_type"], "approval_requested")
            self.assertEqual(events[0]["details"]["approval_id"], "apr_1")

            self.assertTrue(reopened.delete_session("stable-session"))
            self.assertEqual(reopened.list_audit_events("stable-session"), [])
            reopened.close()


class _AuditAgent:
    def __init__(self):
        self.limits = []

    def audit_events(self, limit=100):
        self.limits.append(limit)
        return [{"event_type": "approval_requested"}]


class TestAuditEndpoints(unittest.TestCase):
    def test_api_and_web_query_the_request_session_audit(self):
        request = SimpleNamespace(headers={"x-hellochusquis-session": "audit-session"})
        agent = _AuditAgent()
        with patch.object(api_main, "_require_agent", return_value=agent) as api_get:
            api_response = api_main.get_audit_events(request, limit=7)
        with patch.object(web_server, "_require_agent", return_value=agent) as web_get:
            web_response = web_server.get_audit_events(request, limit=9)

        api_get.assert_called_once_with(request)
        web_get.assert_called_once_with(request)
        self.assertEqual(api_response["events"][0]["event_type"], "approval_requested")
        self.assertEqual(web_response["events"][0]["event_type"], "approval_requested")
        self.assertEqual(agent.limits, [7, 9])


class TestSessionRetention(unittest.TestCase):
    def test_prune_removes_only_oldest_closed_http_sessions(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = SessionManager(Path(directory) / "sessions.db")
            manager.create_session("http", session_id="closed-1")
            manager.create_session("http", session_id="closed-2")
            manager.create_session("http", session_id="closed-3")
            manager.create_session("http", session_id="active-session")
            for session_id in ("closed-1", "closed-2", "closed-3"):
                manager.close_session(session_id)

            self.assertEqual(manager.prune_closed_sessions("http", keep=2), 1)
            self.assertIsNone(manager.get_session("closed-1"))
            self.assertIsNotNone(manager.get_session("closed-2"))
            self.assertIsNotNone(manager.get_session("closed-3"))
            self.assertIsNotNone(manager.get_session("active-session"))
            manager.close()


class TestHistoryRecovery(unittest.TestCase):
    def test_session_manager_returns_recent_messages_in_chronological_order(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = SessionManager(Path(directory) / "sessions.db")
            session_id = manager.create_session("http", session_id="history-session")
            for index in range(5):
                manager.append_message(session_id, "user", f"message-{index}")

            recent = manager.get_recent_history(session_id, limit=2)
            self.assertEqual([item["content"] for item in recent], ["message-3", "message-4"])
            manager.close()

    def test_agent_restores_only_valid_persisted_message_roles(self):
        class _HistorySource:
            def get_recent_history(self, session_id, limit=100):
                return [
                    {"role": "user", "content": "remember this"},
                    {"role": "assistant", "content": "restored"},
                    {"role": "invalid", "content": "skip"},
                ]

        agent = Agent.__new__(Agent)
        agent.history = History()
        agent.session_manager = _HistorySource()
        agent._session_id = "history-session"
        agent._restore_persisted_history()

        self.assertEqual(
            agent.history.get(),
            [
                {"role": "user", "content": "remember this"},
                {"role": "assistant", "content": "restored"},
            ],
        )


class TestApprovalAuditEvents(unittest.TestCase):
    def test_audit_records_redacted_request_decision_and_result(self):
        agent = Agent.__new__(Agent)
        agent.require_approval = True
        agent.approval_manager = ApprovalManager()
        agent._audited_approval_ids = set()
        agent._session_id = "audit-session"
        agent.session_manager = _AuditSessionManager()
        agent._dispatch_tool = lambda *args, **kwargs: ToolResult(
            success=True, output="execution-secret"
        )

        pending = agent._approval_required_result(
            "files",
            {"action": "write", "path": "/tmp/a", "api_key": "top-secret"},
        )
        request_id = pending.error.split("Approval required: ", 1)[1].split(".", 1)[0]
        agent.decide_approval(request_id, approved=True)
        agent.execute_approved(request_id)

        event_types = [event[1] for event in agent.session_manager.events]
        self.assertEqual(event_types, ["approval_requested", "approval_decided", "approval_executed"])
        request_details = agent.session_manager.events[0][2]
        self.assertEqual(request_details["tool_args"]["api_key"], "[REDACTED]")
        self.assertNotIn("top-secret", str(request_details))
        self.assertTrue(agent.session_manager.events[-1][2]["success"])
        completed = agent.approval_manager._requests[request_id]
        self.assertEqual(completed.result_summary, "Action completed successfully")
        self.assertNotIn("execution-secret", completed.result_summary)
        public_request = agent.approval_manager.list_requests(include_finished=True)[0]
        self.assertNotIn("result_summary", public_request)
        self.assertNotIn("execution-secret", str(public_request))


if __name__ == "__main__":
    unittest.main()
