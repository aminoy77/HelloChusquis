"""Regression tests for redaction of sensitive diagnostic data."""

from pathlib import Path
import unittest


class TestSensitiveLogging(unittest.TestCase):
    def test_agent_logs_and_stream_events_use_redacted_tool_arguments(self):
        source = (Path(__file__).parent.parent / "core" / "agent.py").read_text(
            encoding="utf-8"
        )

        self.assertNotIn('"args": tool_args', source)
        self.assertNotIn("json.dumps(tool_args, default=str)", source)
        self.assertGreaterEqual(source.count("safe_tool_args = redact_sensitive_data(tool_args)"), 2)
        self.assertNotIn('"Blocked unsafe command: %s — %s"', source)
        self.assertNotIn('Blocked unsafe command:[/bold red] {cmd}', source)

    def test_sandbox_timeout_log_omits_the_command(self):
        source = (Path(__file__).parent.parent / "core" / "tool_policy.py").read_text(
            encoding="utf-8"
        )

        self.assertNotIn('"Sandbox command timed out after %.1fs: %s"', source)
        self.assertIn('"Sandbox command timed out after %.1fs"', source)
        self.assertNotIn('stderr=f"Command denied by sandbox policy: {command}"', source)
        self.assertIn('stderr="Command denied by sandbox policy."', source)


if __name__ == "__main__":
    unittest.main()
