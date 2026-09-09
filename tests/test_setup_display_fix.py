import unittest
from unittest.mock import patch

from core import setup


class TestSetupDisplayFix(unittest.TestCase):
    def test_show_config_handles_empty_workspace_dirs(self):
        config = {
            "providers": [],
            "settings": {"workspace_dirs": []},
        }
        with patch("core.setup.ensure_config", return_value=config), patch.object(setup.console, "print") as printer:
            result = setup.show_config()

        self.assertIsNone(result)
        output = "\n".join(str(call.args[0]) for call in printer.call_args_list)
        self.assertIn("Workspace: N/A", output)


if __name__ == "__main__":
    unittest.main()
