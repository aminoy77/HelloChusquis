"""close_current_tab must explain why it refused."""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock

from tools.browser import PersistentBrowser


class TestCloseCurrentTabDiagnostics(unittest.TestCase):
    def test_refusal_reports_the_reason(self):
        pb = PersistentBrowser()
        agent = MagicMock()
        agent.close_current_tab = AsyncMock(
            side_effect=RuntimeError("close_current_tab failed: cannot close the last open tab")
        )
        pb._agent = agent

        result = asyncio.run(pb._handle_close_current_tab())

        self.assertFalse(result["success"])
        self.assertIn("last open tab", result.get("error", ""))


if __name__ == "__main__":
    unittest.main()
