"""Headed browser shows an amber cursor so the run is watchable live.

The overlay is a DOM element (init script) updated on every mouse step, plus a
pulse on click. Headless runs skip it: nobody is watching and it costs calls.
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from core.browser_agent import BrowserAgent


class TestCursorOverlay(unittest.TestCase):
    def _agent(self, headless: bool) -> BrowserAgent:
        agent = BrowserAgent()
        agent.config.headless = headless
        agent.page = MagicMock()
        agent.page.evaluate = AsyncMock()
        return agent

    def test_cursor_move_updates_the_overlay_when_headed(self):
        agent = self._agent(headless=False)

        asyncio.run(agent._cursor_move(120, 240))

        args = agent.page.evaluate.await_args
        self.assertEqual(args.args[1], [120, 240])

    def test_cursor_move_is_skipped_when_headless(self):
        agent = self._agent(headless=True)

        asyncio.run(agent._cursor_move(120, 240))

        agent.page.evaluate.assert_not_called()

    def test_cursor_click_pulses_at_the_click_point(self):
        agent = self._agent(headless=False)

        asyncio.run(agent._cursor_click(50, 60))

        args = agent.page.evaluate.await_args
        self.assertEqual(args.args[1], [50, 60])

    def test_click_element_pulses_the_cursor(self):
        agent = BrowserAgent()
        element = MagicMock()
        element.is_visible = AsyncMock(return_value=True)
        element.wait_for = AsyncMock()
        element.bounding_box = AsyncMock(return_value={"x": 10, "y": 10, "width": 20, "height": 10})
        locator = MagicMock()
        locator.count = AsyncMock(return_value=1)
        locator.nth.return_value = element
        agent.page = MagicMock()
        agent.page.get_by_text.return_value = locator
        agent.page.mouse = AsyncMock()
        agent.human_mouse = MagicMock()
        agent.human_mouse.move_to = AsyncMock()
        agent._get_current_mouse_position = AsyncMock(return_value={"x": 0, "y": 0})
        agent._cursor_click = AsyncMock()

        with patch.object(BrowserAgent, "health_check", AsyncMock(return_value=True)):
            ok = asyncio.run(agent.click_element(text="Go"))

        self.assertTrue(ok)
        agent._cursor_click.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
