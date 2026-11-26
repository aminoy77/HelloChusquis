"""Browser actions must report why they failed.

select_option and upload_file swallowed every exception and returned a bare
False, so the agent saw "failed" with no clue whether the selector was wrong,
the option missing, or the path blocked.
"""

import unittest
from unittest.mock import AsyncMock, MagicMock

from core.browser_agent import BrowserAgent
from tools import browser


class TestBrowserActionDiagnostics(unittest.TestCase):
    def test_select_option_reports_the_underlying_error(self):
        agent = BrowserAgent()
        locator = MagicMock()
        locator.select_option = AsyncMock(side_effect=Exception("option not found"))
        agent.page = MagicMock()
        agent.page.locator.return_value = locator

        with self.assertRaises(Exception) as ctx:
            import asyncio

            asyncio.run(agent.select_option("select#x", value="missing"))

        self.assertIn("option not found", str(ctx.exception))

    def test_upload_file_reports_the_underlying_error(self):
        agent = BrowserAgent()
        locator = MagicMock()
        locator.set_input_files = AsyncMock(side_effect=Exception("no file input"))
        agent.page = MagicMock()
        agent.page.locator.return_value = locator

        with self.assertRaises(Exception) as ctx:
            import asyncio

            asyncio.run(agent.upload_file("input[type=file]", "/tmp/x.txt"))

        self.assertIn("no file input", str(ctx.exception))

    def test_handler_surfaces_the_error_to_the_caller(self):
        pb = browser.PersistentBrowser()
        agent = AsyncMock()
        agent.select_option.side_effect = RuntimeError("option not found")
        pb._agent = agent

        import asyncio

        result = asyncio.run(pb._handle_select_option(selector="select#x", value="missing"))

        self.assertFalse(result["success"])
        self.assertIn("option not found", result.get("error", ""))


if __name__ == "__main__":
    unittest.main()
