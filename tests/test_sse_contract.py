"""SSE protocol regression tests."""

import json
import unittest

from api import main as api_main


class _AgentWithTerminalEvent:
    def stream_run(self, message):
        yield {"type": "chunk", "content": message}
        yield {"type": "done"}


class _FailingAgent:
    def stream_run(self, message):
        raise RuntimeError("provider unavailable")
        yield  # Make this a generator for the protocol helper.


class TestSSEContract(unittest.TestCase):
    def test_api_emits_exactly_one_terminal_done_event(self):
        wire_events = list(api_main._sse_generator(_AgentWithTerminalEvent(), "hello"))
        payloads = [json.loads(event.removeprefix("data: ").strip()) for event in wire_events]

        self.assertEqual([payload["type"] for payload in payloads], ["chunk", "done"])

    def test_api_error_event_uses_client_compatible_content_field(self):
        wire_events = list(api_main._sse_generator(_FailingAgent(), "hello"))
        payloads = [json.loads(event.removeprefix("data: ").strip()) for event in wire_events]

        self.assertEqual([payload["type"] for payload in payloads], ["error", "done"])
        self.assertEqual(payloads[0]["content"], "Stream failed. Check server logs.")
        self.assertNotIn("provider unavailable", payloads[0]["content"])


if __name__ == "__main__":
    unittest.main()
