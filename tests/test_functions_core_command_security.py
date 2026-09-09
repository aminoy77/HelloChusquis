"""Regression tests for safe legacy command execution."""

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from core.functions_core import run_command


class TestFunctionsCoreCommandSecurity(unittest.TestCase):
    def test_run_command_never_uses_shell_and_splits_arguments(self):
        completed = SimpleNamespace(returncode=0, stdout=b"ok", stderr=b"")
        with patch("core.functions_core.subprocess.run", return_value=completed) as run:
            result = run_command("echo hello; echo unexpected")

        self.assertTrue(result["success"])
        self.assertEqual(run.call_args.args[0], ["echo", "hello;", "echo", "unexpected"])
        self.assertFalse(run.call_args.kwargs["shell"])


if __name__ == "__main__":
    unittest.main()
