"""Regression tests for bounded media and visualization processes."""

from types import SimpleNamespace
import subprocess
import unittest
from unittest.mock import patch

from tools import tts, visualize


class TestMediaProcessLimits(unittest.TestCase):
    def test_linux_tts_process_has_explicit_timeout(self):
        completed = SimpleNamespace(returncode=0, stdout="", stderr="")

        def record_run(command, **kwargs):
            self.assertEqual(command[0], "espeak")
            self.assertEqual(kwargs["timeout"], tts.TTS_PROCESS_TIMEOUT_SECONDS)
            return completed

        with (
            patch("tools.tts.platform.system", return_value="Linux"),
            patch("tools.tts.subprocess.run", side_effect=record_run),
        ):
            response = tts.run("speak", "bounded speech")

        self.assertIn("Spoken", response)

    def test_dbt_timeout_returns_stable_error(self):
        with (
            patch("tools.visualize.os.path.exists", return_value=True),
            patch("tools.visualize.subprocess.run", side_effect=subprocess.TimeoutExpired(["dbt", "run"], 1)),
        ):
            response = visualize.dbt("run")

        self.assertEqual(response, f"dbt timed out after {visualize.DBT_TIMEOUT_SECONDS} seconds")


if __name__ == "__main__":
    unittest.main()
