"""
Browser automation tools for HelloChusquis.
"""

import asyncio
import json
import re
import base64
from typing import Dict, Any, List, Optional
from pathlib import Path

from core.browser_agent import BrowserAgent, BrowserConfig, create_browser_agent


class BrowserTools:
    """Browser automation tools for HelloChusquis."""

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.agent: Optional[BrowserAgent] = None
        self._is_running = False

    async def _get_agent(self) -> BrowserAgent:
        """Get or create browser agent."""
        if self.agent is None or not self._is_running:
            self.agent = await create_browser_agent(headless=False, slow=True, debug=self.debug)
            self._is_running = True
        return self.agent

    def browser_navigate(self, url: str, wait: bool = True) -> Dict[str, Any]:
        """Navigate to a URL in the browser."""
        return asyncio.get_event_loop().run_until_complete(
            self._browser_navigate_async(url, wait)
        )

    async def _browser_navigate_async(self, url: str, wait: bool) -> Dict[str, Any]:
        """Navigate to URL asynchronously."""
        agent = await self._get_agent()

        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        success = await agent.navigate(url, wait_until='networkidle' if wait else 'domcontentloaded')

        return {
            'success': success,
            'url': agent.state.url,
            'title': agent.state.title,
            'message': f"{'✓' if success else '✗'} Navigated to {agent.state.url}"
        }

    def browser_click(self, selector: str = None, text: str = None, xpath: str = None) -> Dict[str, Any]:
        """Click an element on the page."""
        return asyncio.get_event_loop().run_until_complete(
            self._browser_click_async(selector, text, xpath)
        )

    async def _browser_click_async(self, selector: str = None, text: str = None, xpath: str = None) -> Dict[str, Any]:
        """Click asynchronously."""
        agent = await self._get_agent()

        success = await agent.click_element(selector=selector, text=text, xpath=xpath)

        return {
            'success': success,
            'message': f"{'✓' if success else '✗'} Clicked element"
        }

    def browser_type(self, text: str, selector: str = None) -> Dict[str, Any]:
        """Type text into an element."""
        return asyncio.get_event_loop().run_until_complete(
            self._browser_type_async(text, selector)
        )

    async def _browser_type_async(self, text: str, selector: str = None) -> Dict[str, Any]:
        """Type text asynchronously."""
        agent = await self._get_agent()

        success = await agent.type_text(text, selector=selector)

        return {
            'success': success,
            'message': f"{'✓' if success else '✗'} Typed text"
        }

    def browser_scroll(self, direction: str = 'down', amount: int = 3) -> Dict[str, Any]:
        """Scroll the page."""
        return asyncio.get_event_loop().run_until_complete(
            self._browser_scroll_async(direction, amount)
        )

    async def _browser_scroll_async(self, direction: str, amount: int) -> Dict[str, Any]:
        """Scroll asynchronously."""
        agent = await self._get_agent()

        await agent.scroll(direction=direction, amount=amount)

        return {
            'success': True,
            'message': f"✓ Scrolled {direction} {amount} times"
        }

    def browser_screenshot(self, path: str = None, full_page: bool = False) -> Dict[str, Any]:
        """Take a screenshot."""
        return asyncio.get_event_loop().run_until_complete(
            self._browser_screenshot_async(path, full_page)
        )

    async def _browser_screenshot_async(self, path: str = None, full_page: bool = False) -> Dict[str, Any]:
        """Take screenshot asynchronously."""
        agent = await self._get_agent()

        if not path:
            path = 'browser_screenshot.png'

        screenshot_path = await agent.save_screenshot(path)

        if screenshot_path:
            with open(screenshot_path, 'rb') as f:
                img_data = base64.b64encode(f.read()).decode()

            return {
                'success': True,
                'path': screenshot_path,
                'base64': img_data[:100] + '...',
                'message': f"✓ Screenshot saved to {screenshot_path}"
            }

        return {
            'success': False,
            'message': '✗ Failed to take screenshot'
        }

    def browser_get_text(self, selector: str = None) -> Dict[str, Any]:
        """Get text content from page or element."""
        return asyncio.get_event_loop().run_until_complete(
            self._browser_get_text_async(selector)
        )

    async def _browser_get_text_async(self, selector: str = None) -> Dict[str, Any]:
        """Get text asynchronously."""
        agent = await self._get_agent()

        text = await agent.get_text_content(selector)

        return {
            'success': True,
            'text': text[:5000],  # Limit text length
            'message': f"✓ Got text content ({len(text)} chars)"
        }

    def browser_search(self, query: str, engine: str = 'google') -> Dict[str, Any]:
        """Search using a search engine."""
        return asyncio.get_event_loop().run_until_complete(
            self._browser_search_async(query, engine)
        )

    async def _browser_search_async(self, query: str, engine: str) -> Dict[str, Any]:
        """Search asynchronously."""
        agent = await self._get_agent()

        success = await agent.search(engine, query)

        return {
            'success': success,
            'url': agent.state.url,
            'title': agent.state.title,
            'message': f"✓ Searched '{query}' on {engine}"
        }

    def browser_find(self, pattern: str) -> Dict[str, Any]:
        """Find elements matching pattern."""
        return asyncio.get_event_loop().run_until_complete(
            self._browser_find_async(pattern)
        )

    async def _browser_find_async(self, pattern: str) -> Dict[str, Any]:
        """Find elements asynchronously."""
        agent = await self._get_agent()

        results = await agent.find_elements(pattern)

        return {
            'success': True,
            'count': len(results),
            'elements': results[:20],  # Limit results
            'message': f"✓ Found {len(results)} elements matching '{pattern}'"
        }

    def browser_fill_form(self, form_data: Dict[str, str]) -> Dict[str, Any]:
        """Fill a form with data."""
        return asyncio.get_event_loop().run_until_complete(
            self._browser_fill_form_async(form_data)
        )

    async def _browser_fill_form_async(self, form_data: Dict[str, str]) -> Dict[str, Any]:
        """Fill form asynchronously."""
        agent = await self._get_agent()

        success = await agent.fill_form(form_data)

        return {
            'success': success,
            'message': f"{'✓' if success else '✗'} Form filled"
        }

    def browser_wait(self, selector: str, timeout: int = 30) -> Dict[str, Any]:
        """Wait for an element to appear."""
        return asyncio.get_event_loop().run_until_complete(
            self._browser_wait_async(selector, timeout)
        )

    async def _browser_wait_async(self, selector: str, timeout: int) -> Dict[str, Any]:
        """Wait for element asynchronously."""
        agent = await self._get_agent()

        success = await agent.wait_for_element(selector, timeout)

        return {
            'success': success,
            'message': f"{'✓' if success else '✗'} Element {'found' if success else 'not found'}"
        }

    def browser_execute(self, script: str) -> Dict[str, Any]:
        """Execute JavaScript on the page."""
        return asyncio.get_event_loop().run_until_complete(
            self._browser_execute_async(script)
        )

    async def _browser_execute_async(self, script: str) -> Dict[str, Any]:
        """Execute script asynchronously."""
        agent = await self._get_agent()

        result = await agent.execute_script(script)

        return {
            'success': result is not None,
            'result': str(result)[:1000] if result else None,
            'message': f"✓ Script executed"
        }

    def browser_close(self) -> Dict[str, Any]:
        """Close the browser."""
        return asyncio.get_event_loop().run_until_complete(
            self._browser_close_async()
        )

    async def _browser_close_async(self) -> Dict[str, Any]:
        """Close browser asynchronously."""
        if self.agent:
            await self.agent.close()
            self.agent = None
            self._is_running = False

        return {
            'success': True,
            'message': '✓ Browser closed'
        }

    def browser_explore(self, start_url: str, task: str) -> Dict[str, Any]:
        """Explore a website and gather information based on a task."""
        return asyncio.get_event_loop().run_until_complete(
            self._browser_explore_async(start_url, task)
        )

    async def _browser_explore_async(self, start_url: str, task: str) -> Dict[str, Any]:
        """Explore website asynchronously."""
        agent = await self._get_agent()

        # Navigate to start
        if not start_url.startswith(('http://', 'https://')):
            start_url = 'https://' + start_url

        await agent.navigate(start_url)
        await asyncio.sleep(2)

        # Take initial screenshot
        await agent.save_screenshot('explore_start.png')

        results = {
            'success': True,
            'url': agent.state.url,
            'title': agent.state.title,
            'screenshots': ['explore_start.png'],
            'found_items': []
        }

        # Based on task, perform appropriate actions
        task_lower = task.lower()

        if 'click' in task_lower or 'button' in task_lower:
            # Find and report clickable elements
            elements = await agent.find_elements('button|click|submitted')
            results['clickable_elements'] = elements[:10]

        if 'search' in task_lower:
            # If we need to search
            search_pattern = task.replace('search', '').replace('find', '').strip()
            elements = await agent.find_elements(search_pattern)
            results['found_items'] = elements[:10]

        # Get page content summary
        text = await agent.get_text_content()
        results['page_text'] = text[:2000]

        return results


# Global instance for function-based access
_browser_tools = None


def get_browser_tools(debug: bool = False) -> BrowserTools:
    """Get or create browser tools instance."""
    global _browser_tools
    if _browser_tools is None:
        _browser_tools = BrowserTools(debug=debug)
    return _browser_tools


# Synchronous wrappers for use in functions
def navigate_to_url(url: str) -> Dict[str, Any]:
    """Navigate to URL."""
    tools = get_browser_tools()
    return tools.browser_navigate(url)


def click_element(selector: str = None, text: str = None) -> Dict[str, Any]:
    """Click element."""
    tools = get_browser_tools()
    return tools.browser_click(selector, text)


def input_text(text: str, selector: str = None) -> Dict[str, Any]:
    """Input text."""
    tools = get_browser_tools()
    return tools.browser_type(text, selector)


def scroll_page(direction: str = 'down', amount: int = 3) -> Dict[str, Any]:
    """Scroll page."""
    tools = get_browser_tools()
    return tools.browser_scroll(direction, amount)


def take_screenshot(path: str = None) -> Dict[str, Any]:
    """Take screenshot."""
    tools = get_browser_tools()
    return tools.browser_screenshot(path)


def get_content(selector: str = None) -> Dict[str, Any]:
    """Get page content."""
    tools = get_browser_tools()
    return tools.browser_get_text(selector)


def search_web(query: str, engine: str = 'google') -> Dict[str, Any]:
    """Search the web."""
    tools = get_browser_tools()
    return tools.browser_search(query, engine)


def close_browser() -> Dict[str, Any]:
    """Close browser."""
    tools = get_browser_tools()
    return tools.browser_close()