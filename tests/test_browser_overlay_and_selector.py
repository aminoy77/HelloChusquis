"""Cursor overlay must survive Trusted Types and hidden duplicate selectors."""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from core.browser_agent import BrowserAgent, _CURSOR_OVERLAY_JS


class TestOverlayTrustedTypes(unittest.TestCase):
    def test_overlay_never_uses_inner_html(self):
        # YouTube/Gmail enforce Trusted Types: innerHTML throws, so the whole
        # mount aborted and the amber cursor never appeared.
        self.assertNotIn("innerHTML", _CURSOR_OVERLAY_JS)
        self.assertIn("createElementNS", _CURSOR_OVERLAY_JS)


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


class TestSelectorPicksVisibleElement(unittest.TestCase):
    def _agent(self, elements):
        agent = BrowserAgent()
        page = MagicMock()
        page.locator.return_value = _Locator(elements)
        page.mouse = AsyncMock()
        agent.page = page
        agent.human_mouse = MagicMock()
        agent.human_mouse.move_to = AsyncMock()
        agent._get_current_mouse_position = AsyncMock(return_value={"x": 0, "y": 0})
        return agent

    def test_hidden_css_duplicate_is_skipped(self):
        hidden = _Element(visible=False)
        visible = _Element(visible=True)
        agent = self._agent([hidden, visible])

        with patch.object(BrowserAgent, "health_check", AsyncMock(return_value=True)):
            ok = asyncio.run(agent.click_element(selector="input#search"))

        self.assertTrue(ok)
        self.assertTrue(page_clicked := agent.page.mouse.click.called)
        self.assertTrue(page_clicked)

    def test_failure_reports_a_reason(self):
        hidden = _Element(visible=False)
        agent = self._agent([hidden])

        with patch.object(BrowserAgent, "health_check", AsyncMock(return_value=True)):
            ok = asyncio.run(agent.click_element(selector="input#search"))

        self.assertFalse(ok)
        self.assertTrue(agent.state.last_error)


if __name__ == "__main__":
    unittest.main()
