import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from core.browser_agent import BrowserAgent


class TestBrowserStartupCleanup(unittest.TestCase):
    def test_failed_launch_cleans_up_partial_playwright_state(self):
        playwright = SimpleNamespace(
            chromium=SimpleNamespace(
                launch=AsyncMock(side_effect=RuntimeError("launch failed")),
            )
        )
        manager = SimpleNamespace(start=AsyncMock(return_value=playwright))
        agent = BrowserAgent()

        with patch("playwright.async_api.async_playwright", return_value=manager), patch.object(
            agent, "close", new=AsyncMock()
        ) as close:
            started = asyncio.run(agent.start())

        self.assertFalse(started)
        close.assert_awaited_once_with()

    def test_missing_executable_is_fatal_not_retried(self):
        playwright = SimpleNamespace(
            chromium=SimpleNamespace(
                launch=AsyncMock(
                    side_effect=Exception("Executable doesn't exist at /cache/ms-playwright")
                ),
            )
        )
        manager = SimpleNamespace(start=AsyncMock(return_value=playwright))
        agent = BrowserAgent()

        with patch("playwright.async_api.async_playwright", return_value=manager), patch.object(
            agent, "close", new=AsyncMock()
        ):
            started = asyncio.run(agent.start())

        self.assertFalse(started)
        self.assertIn("playwright install", agent.start_fatal)


if __name__ == "__main__":
    unittest.main()
