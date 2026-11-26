import json
import unittest

from api import main as api_main


class _AgentFailsAfterDone:
    def stream_run(self, message, provider=None, model=None):
        yield {"type": "done"}
        raise RuntimeError("late provider failure")


class TestTargetedImprovements(unittest.TestCase):
    def test_sse_does_not_emit_error_after_terminal_done(self):
        wire_events = list(api_main._sse_generator(_AgentFailsAfterDone(), "hello"))
        payloads = [json.loads(event.removeprefix("data: ").strip()) for event in wire_events]

        self.assertEqual([payload["type"] for payload in payloads], ["done"])


if __name__ == "__main__":
    unittest.main()
