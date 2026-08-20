"""Conversation turn serialization regression tests."""

import json
import threading
import unittest

from api import main as api_main
from core.agent import Agent


class _StreamingAgent:
    def __init__(self):
        self.releases = 0

    def stream_run(self, message):
        yield {"type": "done"}

    def release_turn(self):
        self.releases += 1


class TestTurnSerialization(unittest.TestCase):
    def test_agent_allows_only_one_active_turn(self):
        agent = Agent.__new__(Agent)
        agent._turn_lock = threading.Lock()

        self.assertTrue(agent.try_acquire_turn())
        self.assertFalse(agent.try_acquire_turn())
        agent.release_turn()
        self.assertTrue(agent.try_acquire_turn())
        agent.release_turn()

    def test_sse_releases_acquired_turn_after_terminal_event(self):
        agent = _StreamingAgent()
        events = list(api_main._sse_generator(agent, "hello", release_turn=True))
        payloads = [json.loads(event.removeprefix("data: ").strip()) for event in events]

        self.assertEqual([event["type"] for event in payloads], ["done"])
        self.assertEqual(agent.releases, 1)


if __name__ == "__main__":
    unittest.main()
