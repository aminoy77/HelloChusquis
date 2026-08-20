"""Regression tests for request-local web tool logging."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from tools.base import ToolResult
from web import server as web_server


class _FakeHistory:
    def clear(self):
        return None


class _FakeAgent:
    def __init__(self):
        self.history = _FakeHistory()
        self._dispatch_tool = object()
        self.turn_releases = 0

    def try_acquire_turn(self):
        return True

    def release_turn(self):
        self.turn_releases += 1

    def run(self, user_input, provider=None, model=None, tool_result_callback=None):
        if callable(tool_result_callback):
            tool_result_callback(
                "files",
                {"action": "list"},
                ToolResult(success=True, output="workspace contents"),
            )
        return "completed"


class TestWebRequestIsolation(unittest.TestCase):
    def test_chat_logs_tools_without_mutating_shared_dispatcher(self):
        fake_agent = _FakeAgent()
        original_dispatcher = fake_agent._dispatch_tool
        request = SimpleNamespace(message="list files", provider=None, model=None)
        http_request = SimpleNamespace(
            client=SimpleNamespace(host="isolation-test"),
            headers={"x-hellochusquis-session": "isolation-test"},
        )

        with patch.object(web_server.runtime, "_agent", fake_agent), patch.object(
            web_server.runtime, "_error", None
        ):
            response = web_server.chat(request, http_request)

        self.assertEqual(response["response"], "completed")
        self.assertEqual(response["tool_calls"], [{
            "tool": "files",
            "args": {"action": "list"},
            "success": True,
            "output": "workspace contents",
        }])
        self.assertIs(fake_agent._dispatch_tool, original_dispatcher)
        self.assertEqual(fake_agent.turn_releases, 1)

    def test_web_auth_is_enabled_by_default(self):
        self.assertTrue(web_server.AUTH_ENABLED)


if __name__ == "__main__":
    unittest.main()
