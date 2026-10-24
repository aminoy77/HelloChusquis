"""Hallucinated tool names stay out of the UI: no event, no console noise."""
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import core.db_memory as db_memory
from core.agent import Agent
from core.history import History


class _FakeLoop:
    def record_call(self, *args):
        pass


def _agent(pool):
    agent = Agent.__new__(Agent)
    agent.pool = pool
    agent.history = History()
    agent.session_manager = SimpleNamespace(append_message=lambda *a: None)
    agent.system_prompt = ""
    agent.workspace_dirs = []
    agent.skills = SimpleNamespace(skills_prompt_section=lambda: "")
    agent.plugins = []
    agent.role = None
    agent._session_id = "test-session"
    agent._pending_tool_results = []
    agent._loop_session_state = object()
    agent.loop_detector = _FakeLoop()
    agent.tools_schema = [
        {"type": "function", "function": {"name": "shell", "description": "x"}},
    ]
    agent._external_tool_modules = {}
    return agent


class TestUnknownToolSilenced(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._prev = db_memory.MEMORY_DB_PATH
        from pathlib import Path
        db_memory.MEMORY_DB_PATH = Path(self._tmp) / "t.db"

    def tearDown(self):
        db_memory.MEMORY_DB_PATH = self._prev
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_known_names_cover_schema(self):
        agent = _agent(pool=None)
        self.assertIn("shell", agent._known_tool_names())
        self.assertNotIn("list_functions", agent._known_tool_names())
        self.assertNotIn("build", agent._known_tool_names())

    def test_stream_skips_event_for_unknown_tool(self):
        calls = [
            [{"type": "tool_calls", "tool_calls": [
                {"id": "1", "function": {"name": "list_functions", "arguments": "{}"}},
                {"id": "2", "function": {"name": "build", "arguments": "{}"}},
            ]}],
            [{"type": "chunk", "content": "done"}],
        ]

        def fake_stream(*a, **k):
            yield from calls.pop(0)

        pool = SimpleNamespace(chat_stream=fake_stream)
        agent = _agent(pool)
        with patch("core.agent.print_tool_call") as ptc:
            events = list(agent.stream_run("list functions"))
        kinds = [e["type"] for e in events]
        self.assertNotIn("tool_call", kinds)
        self.assertIn("done", kinds)
        ptc.assert_not_called()


if __name__ == "__main__":
    unittest.main()
