"""User-experience regressions for the command-line interface."""

import sys
import unittest
from unittest.mock import patch

import cli
import main as main_module


class TestCliUserExperience(unittest.TestCase):
    def test_config_opens_browser_setup_by_default(self):
        with patch.object(sys, "argv", ["hellochusquis", "config"]), patch(
            "web.setup.run_setup_frontend"
        ) as setup_frontend:
            cli.main()

        setup_frontend.assert_called_once_with()

    def test_first_launch_opens_browser_setup(self):
        config = {"providers": [], "settings": {"memory_retention_days": 30}}
        agent = object()
        with patch("main.ensure_config", side_effect=FileNotFoundError), patch(
            "web.setup.run_setup_frontend", return_value=config
        ) as setup_frontend, patch("main.Agent", return_value=agent), patch(
            "main._cleanup"
        ) as cleanup, patch("ui.tui.run_tui") as run_tui, patch("main.signal.signal"):
            main_module.main()

        setup_frontend.assert_called_once_with()
        run_tui.assert_called_once_with(agent=agent, config=config)
        cleanup.assert_called_once_with(agent, 30)

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
