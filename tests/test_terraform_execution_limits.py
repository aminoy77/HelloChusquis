"""Regression tests for bounded Terraform process execution."""

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import terraform


class TestTerraformExecutionLimits(unittest.TestCase):
    def test_terraform_process_uses_explicit_timeout(self):
        completed = SimpleNamespace(stdout="ok", stderr="")
        with patch("tools.terraform.subprocess.run", return_value=completed) as run:
            result = terraform.run("plan", directory=".")

        self.assertEqual(result, "ok")
        self.assertEqual(run.call_args.kwargs["timeout"], terraform.TERRAFORM_TIMEOUT_SECONDS)


if __name__ == "__main__":
    unittest.main()
