"""Clicking by text must not fail because a hidden element matched first.

get_by_text() returned hidden and visible matches; the code always took
nth(index), so a hidden duplicate made the click fail even when a visible
element with the same text existed.
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from core.browser_agent import BrowserAgent


class _Locator:
    def __init__(self, elements):
        self._elements = elements

    async def count(self):
        return len(self._elements)

    def nth(self, index):
        return self._elements[index]


class _Element:
    def __init__(self, visible):
        self._visible = visible
        self.clicked = False

    async def is_visible(self):
        return self._visible

    async def wait_for(self, state=None, timeout=None):
        if not self._visible:
            raise RuntimeError("not visible")

    async def bounding_box(self):
        return {"x": 10, "y": 10, "width": 20, "height": 10}

    async def click(self, timeout=None):
        self.clicked = True


class TestClickByTextPicksVisibleElement(unittest.TestCase):
    def test_hidden_match_is_skipped_in_favour_of_visible_one(self):
        agent = BrowserAgent()
        hidden = _Element(visible=False)
        visible = _Element(visible=True)
        page = MagicMock()
        page.get_by_text.return_value = _Locator([hidden, visible])
        page.mouse = AsyncMock()
        agent.page = page
        agent.human_mouse = MagicMock()
        agent.human_mouse.move_to = AsyncMock()
        agent._get_current_mouse_position = AsyncMock(return_value={"x": 0, "y": 0})

        with patch.object(BrowserAgent, "health_check", AsyncMock(return_value=True)):
            ok = asyncio.run(agent.click_element(text="Target Button"))

        self.assertTrue(ok)
        self.assertTrue(visible.clicked or page.mouse.click.called)


if __name__ == "__main__":
    unittest.main()
