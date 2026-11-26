"""Regressions from the live YouTube cookie/cursor run."""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock

from core.browser_agent import BrowserAgent
from tools.browser import PersistentBrowser


class _Locator:
    def __init__(self, elements):
        self._elements = elements

    async def count(self):
        return len(self._elements)

    def nth(self, i):
        return self._elements[i]


class _Element:
    def __init__(self, visible):
        self._visible = visible

    async def is_visible(self):
        return self._visible

    async def wait_for(self, state=None, timeout=None):
        if not self._visible:
            raise RuntimeError("not visible")

    async def bounding_box(self):
        return {"x": 10, "y": 10, "width": 20, "height": 10}


class TestExactTextClick(unittest.TestCase):
    def test_click_by_text_prefers_exact_match(self):
        agent = BrowserAgent()
        button = _Element(visible=True)
        page = MagicMock()
        page.get_by_text.side_effect = lambda text, exact: (
            _Locator([button]) if exact else _Locator([_Element(visible=True)])
        )
        page.mouse = AsyncMock()
        agent.page = page
        agent.human_mouse = MagicMock()
        agent.human_mouse.move_to = AsyncMock()
        agent._get_current_mouse_position = AsyncMock(return_value={"x": 0, "y": 0})
        agent.config = MagicMock()
        agent.config.action_timeout = 1000

        with unittest.mock.patch.object(
            BrowserAgent, "health_check", AsyncMock(return_value=True)
        ):
            ok = asyncio.run(agent.click_element(text="Reject all"))

        self.assertTrue(ok)
        self.assertEqual(page.get_by_text.call_args_list[0].kwargs, {"exact": True})
        self.assertTrue(page.mouse.click.called)


class TestExecuteScriptReturn(unittest.IsolatedAsyncioTestCase):
    async def test_function_body_with_return_is_retried_as_iife(self):
        agent = BrowserAgent()
        page = MagicMock()
        page.evaluate = AsyncMock(
            side_effect=[RuntimeError("SyntaxError: Illegal return statement"), "ok"]
        )
        agent.page = page

        self.assertEqual(await agent.execute_script("return document.title;"), "ok")
        self.assertIn("return document.title;", page.evaluate.await_args_list[1].args[0])


class TestClickDiagnostics(unittest.IsolatedAsyncioTestCase):
    async def test_click_failure_reports_the_reason(self):
        pb = PersistentBrowser()
        agent = MagicMock()
        agent.click_element = AsyncMock(return_value=False)
        agent.state.last_error = "element not visible after 15000ms"
        pb._agent = agent

        result = await pb._handle_click(selector="input#search")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "element not visible after 15000ms")


if __name__ == "__main__":
    unittest.main()
