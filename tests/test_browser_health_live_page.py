"""Browser health must report the live page, not stale cached state.

state.url/state.title are only updated by page-load events, so after a tab
switch the health endpoint reported the previous tab's URL.
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock

from tools.browser import PersistentBrowser


class TestBrowserHealthUsesLivePage(unittest.TestCase):
    def test_health_reports_live_page_url_and_title(self):
        pb = PersistentBrowser()
        agent = MagicMock()
        agent.state.url = "https://old.example/"
        agent.state.title = "Old"
        agent.health_check = AsyncMock(return_value=True)
        page = MagicMock()
        page.url = "https://new.example/"
        page.title = AsyncMock(return_value="New")
        agent.page = page
        agent.context.pages = [page]
        pb._agent = agent

        result = asyncio.run(pb._handle_health())

        self.assertEqual(result["url"], "https://new.example/")
        self.assertEqual(result["title"], "New")


if __name__ == "__main__":
    unittest.main()
