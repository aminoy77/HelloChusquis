"""Security regressions for workflow built-in actions."""

import unittest
from unittest.mock import patch

from core.workflow_engine import WorkflowEngine, WorkflowStep


class TestWorkflowEngineSecurity(unittest.TestCase):
    def test_shell_step_does_not_bypass_the_shared_shell_safety_gate(self):
        engine = WorkflowEngine()
        step = WorkflowStep(name="unsafe", action="shell", params={"command": "rm -rf /"})

        success, result = engine.execute_step(step, {})

        self.assertFalse(success)
        self.assertIn("Blocked", result)

    def test_http_step_blocks_private_destination_before_network_request(self):
        engine = WorkflowEngine()
        step = WorkflowStep(
            name="metadata",
            action="http",
            params={"url": "http://127.0.0.1:8080/private"},
        )

        with patch("httpx.request") as request:
            success, result = engine.execute_step(step, {})

        self.assertFalse(success)
        self.assertIn("SSRF blocked", result)
        request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
