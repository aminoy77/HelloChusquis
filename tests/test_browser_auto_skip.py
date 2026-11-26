"""Idle housekeeping: ads, intros, consent dialogs, paused video, page report."""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock

from core.browser_agent import BrowserAgent


class _Locator:
    def __init__(self, elements):
        self._elements = elements

    async def count(self):
        return len(self._elements)

    def nth(self, i):
        return self._elements[i]


class _Element:
    def __init__(self, visible=True):
        self._visible = visible
        self.clicked = False

    async def is_visible(self):
        return self._visible

    async def bounding_box(self):
        return {"x": 100, "y": 200, "width": 40, "height": 20}

    async def click(self, timeout=None):
        self.clicked = True


def _agent(locators, played=False, report=None):
    agent = BrowserAgent.__new__(BrowserAgent)
    page = MagicMock()
    page.locator.side_effect = [_Locator(x) for x in locators]
    page.evaluate = AsyncMock(return_value=played if not report else report)
    agent.page = page
    agent.config = type("C", (), {"headless": False})()
    agent._cursor_move = AsyncMock()
    agent._cursor_click = AsyncMock()
    return agent


class TestAutoHandle(unittest.TestCase):
    def test_clicks_the_first_visible_skip_button(self):
        button = _Element()
        agent = _agent([[button]] + [[]] * 5)

        actions = asyncio.run(agent.auto_handle())

        self.assertTrue(button.clicked)
        self.assertTrue(actions)
        agent._cursor_move.assert_awaited_once_with(120, 210)
        agent._cursor_click.assert_awaited_once_with(120, 210)

    def test_clicks_reject_all_in_a_consent_dialog(self):
        reject = _Element()
        agent = _agent([[], [], [], [reject], [], []])

        actions = asyncio.run(agent.auto_handle())

        self.assertTrue(reject.clicked)
        self.assertTrue(any("Reject all" in a for a in actions))

    def test_ignores_hidden_buttons(self):
        hidden = _Element(visible=False)
        agent = _agent([[hidden]] + [[]] * 5)

        self.assertFalse(any(asyncio.run(agent.auto_handle())))
        self.assertFalse(hidden.clicked)

    def test_resumes_a_paused_video(self):
        agent = _agent([[]] * 6, played=True)

        actions = asyncio.run(agent.auto_handle())

        self.assertIn("play video", actions)

    def test_page_report_returns_the_structured_summary(self):
        report = {"title": "X", "links": [], "video": {"paused": False}}
        agent = _agent([], report=report)

        self.assertEqual(asyncio.run(agent.page_report()), report)


if __name__ == "__main__":
    unittest.main()
