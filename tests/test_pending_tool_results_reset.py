"""Audit #4: a failed turn must not leak orphan tool messages into the next
turn (providers reject a tool message without its assistant tool_calls)."""
import os
import sys
import unittest
import unittest.mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.agent import Agent


def _agent():
    config = {
        "providers": [{
            "name": "fake", "base_url": "http://127.0.0.1:9/v1",
            "api_key": "k", "model": "m",
        }],
        "settings": {},
    }
    return Agent(config)


class TestPendingToolResultsReset(unittest.TestCase):
    def test_run_clears_stale_pending_at_turn_start(self):
        agent = _agent()
        agent._pending_tool_results = [
            {"role": "tool", "tool_call_id": "x", "content": "stale"}]
        # Provider unreachable -> turn fails; the important part is that the
        # NEXT turn's message list must not contain the orphan tool message.
        with unittest.mock.patch.object(
                agent.pool, "chat_with_retry",
                side_effect=RuntimeError("provider down")):
            with self.assertRaises(RuntimeError):
                agent.run("hi")
        self.assertEqual(agent._pending_tool_results, [])

    def test_stream_run_clears_stale_pending_at_turn_start(self):
        agent = _agent()
        agent._pending_tool_results = [
            {"role": "tool", "tool_call_id": "x", "content": "stale"}]
        with unittest.mock.patch.object(
                agent.pool, "chat_stream",
                side_effect=RuntimeError("provider down")):
            with self.assertRaises(RuntimeError):
                list(agent.stream_run("hi"))
        self.assertEqual(agent._pending_tool_results, [])


if __name__ == "__main__":
    unittest.main()
