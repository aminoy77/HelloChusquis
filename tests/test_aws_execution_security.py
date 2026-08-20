"""Regression tests for bounded and private AWS CLI execution."""

from pathlib import Path
from types import SimpleNamespace
import stat
import unittest
from unittest.mock import patch

from tools import aws


class TestAwsExecutionSecurity(unittest.TestCase):
    def test_lambda_payload_uses_private_temporary_file_and_bounded_command(self):
        captured_payload_files: list[Path] = []
        completed = SimpleNamespace(returncode=0, stdout='{"StatusCode": 200}', stderr="")

        def record_run(command, **kwargs):
            self.assertEqual(kwargs["timeout"], 60)
            payload_index = command.index("--payload") + 1
            payload_argument = command[payload_index]
            self.assertTrue(payload_argument.startswith("fileb://"))
            payload_path = Path(payload_argument.removeprefix("fileb://"))
            captured_payload_files.append(payload_path)
            self.assertTrue(payload_path.exists())
            self.assertEqual(stat.S_IMODE(payload_path.stat().st_mode), 0o600)
            self.assertEqual(payload_path.read_text(encoding="utf-8"), '{"token": "secret-value"}')
            return completed

        with (
            patch("tools.aws.get_aws_credentials", return_value={"access_key": "id", "secret_key": "key", "region": "us-east-1"}),
            patch("tools.aws.subprocess.run", side_effect=record_run),
        ):
            response = aws.run("invoke_lambda", resource="example", payload='{"token": "secret-value"}')

        self.assertIn("Lambda invoked", response)
        self.assertEqual(len(captured_payload_files), 1)
        self.assertFalse(captured_payload_files[0].exists())


if __name__ == "__main__":
    unittest.main()
