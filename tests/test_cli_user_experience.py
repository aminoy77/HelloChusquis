"""User-experience regressions for the command-line interface."""

import sys
import unittest
from unittest.mock import patch

import cli


class TestCliUserExperience(unittest.TestCase):
    def test_status_is_a_recognized_command_before_setup(self):
        with patch.object(sys, "argv", ["hellochusquis", "status"]), patch(
            "core.setup.ensure_config", side_effect=FileNotFoundError
        ), patch("builtins.print") as printer:
            cli.main()

        output = "\n".join(str(call.args[0]) for call in printer.call_args_list)
        self.assertIn("setup required", output.lower())
        self.assertNotIn("Unknown command", output)

    def test_status_contracts_runs_without_configuration(self):
        with patch.object(sys, "argv", ["hellochusquis", "status", "--contracts"]), patch(
            "core.setup.ensure_config", side_effect=FileNotFoundError
        ), patch(
            "core.integration_contracts.check_integration_contracts", return_value=[]
        ), patch(
            "core.integration_contracts.contract_summary",
            return_value={"passed": 0, "total": 0, "failed": 0},
        ), patch("builtins.print") as printer:
            cli.main()

        output = "\n".join(str(call.args[0]) for call in printer.call_args_list)
        self.assertIn("setup required", output.lower())
        self.assertIn("Integration contracts: 0/0 passed", output)

    def test_api_defaults_to_loopback_host(self):
        with patch.object(sys, "argv", ["hellochusquis", "api"]), patch(
            "uvicorn.run"
        ) as run:
            cli.main()

        self.assertEqual(run.call_args.kwargs["host"], "127.0.0.1")
        self.assertEqual(run.call_args.kwargs["port"], 8080)


if __name__ == "__main__":
    unittest.main()
