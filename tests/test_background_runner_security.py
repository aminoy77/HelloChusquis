"""Regression tests for safe background process lifecycle management."""

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from core.runner import BackgroundRunner, BackgroundTask


class TestBackgroundRunnerSecurity(unittest.TestCase):
    def test_start_uses_isolated_environment_without_shell_or_output_pipes(self):
        runner = BackgroundRunner()
        runner.register(BackgroundTask(name="worker", command="python worker.py", environment={"WORKER_MODE": "safe"}))
        process = SimpleNamespace(pid=123, poll=lambda: None)

        with patch("core.runner.subprocess.Popen", return_value=process) as popen:
            response = runner.start("worker")

        self.assertTrue(response["success"])
        command = popen.call_args.args[0]
        options = popen.call_args.kwargs
        self.assertEqual(command, ["python", "worker.py"])
        self.assertFalse(options["shell"])
        self.assertTrue(options["start_new_session"])
        self.assertIs(options["stdout"], __import__("subprocess").DEVNULL)
        self.assertIs(options["stderr"], __import__("subprocess").DEVNULL)
        self.assertEqual(options["env"]["WORKER_MODE"], "safe")
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", options["env"])

    def test_status_marks_finished_process_as_not_running(self):
        runner = BackgroundRunner()
        task = BackgroundTask(name="finished", command="echo done", _running=True)
        task._process = SimpleNamespace(pid=456, poll=lambda: 0)
        runner.register(task)

        status = runner.status("finished")

        self.assertFalse(status["running"])
        self.assertIsNone(status["pid"])


if __name__ == "__main__":
    unittest.main()
