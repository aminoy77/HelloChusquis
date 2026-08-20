"""Tests for human approval controls on high-impact tool calls."""

from __future__ import annotations

import unittest

from core.approvals import ApprovalManager, ApprovalStatus, approval_reason


class _Clock:
    def __init__(self, value=1000.0):
        self.value = value

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


class TestApprovalClassification(unittest.TestCase):
    def test_read_only_file_operation_does_not_need_approval(self):
        self.assertIsNone(approval_reason("files", {"action": "read", "path": "/tmp/a"}))

    def test_shell_and_external_mutation_need_approval(self):
        self.assertIsNotNone(approval_reason("shell", {"command": "echo hello"}))
        self.assertIsNotNone(approval_reason("github", {"action": "create_issue"}))


class TestApprovalManager(unittest.TestCase):
    def setUp(self):
        self.clock = _Clock()
        self.manager = ApprovalManager(ttl_seconds=30, max_requests=3, clock=self.clock)

    def test_deduplicates_identical_pending_call(self):
        first = self.manager.request_for("files", {"action": "delete", "path": "/tmp/a"})
        second = self.manager.request_for("files", {"action": "delete", "path": "/tmp/a"})

        self.assertIsNotNone(first)
        self.assertEqual(first.id, second.id)
        self.assertEqual(len(self.manager.list_requests()), 1)

    def test_denied_request_cannot_be_executed(self):
        request = self.manager.request_for("shell", {"command": "echo hello"})
        self.manager.decide(request.id, approved=False)

        with self.assertRaisesRegex(ValueError, "not approved"):
            self.manager.claim_execution(request.id)

    def test_approved_request_is_single_use(self):
        request = self.manager.request_for("code", {"code": "print('ok')"})
        self.manager.decide(request.id, approved=True)
        claimed = self.manager.claim_execution(request.id)
        completed = self.manager.complete_execution(claimed.id, success=True, summary="ok")

        self.assertEqual(completed.status, ApprovalStatus.EXECUTED)
        self.assertEqual(completed.result_summary, "ok")
        with self.assertRaisesRegex(ValueError, "not approved"):
            self.manager.claim_execution(request.id)

    def test_pending_request_expires(self):
        request = self.manager.request_for("shell", {"command": "date"})
        self.clock.advance(31)

        self.assertEqual(self.manager.list_requests(), [])
        with self.assertRaisesRegex(ValueError, "expired"):
            self.manager.decide(request.id, approved=True)

    def test_public_request_redacts_credential_fields(self):
        self.manager.request_for(
            "github",
            {"action": "create_issue", "token": "secret-value", "title": "Bug"},
        )

        public_request = self.manager.list_requests()[0]

        self.assertEqual(public_request["tool_args"]["token"], "[REDACTED]")
        self.assertEqual(public_request["tool_args"]["title"], "Bug")


if __name__ == "__main__":
    unittest.main()
