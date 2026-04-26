"""
Browser Controller Agent
Controls a browser instance for web exploration.
"""

import asyncio
import base64
import io
import json
import os
import random
import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable, Any
from pathlib import Path

import requests

from core.human_mouse import get_human_mouse, HumanMouse, get_cautious_human_mouse


@dataclass
class BrowserConfig:
    """Configuration for browser automation."""
    headless: bool = False
    window_width: int = 1280
    window_height: int = 800
    user_agent: str = None
    accept_downloads: bool = False
    slow_mo: int = 0
    stealth: bool = True  # Avoid detection

    @classmethod
    def default(cls):
        return cls()


@dataclass
class BrowserState:
    """Current state of the browser."""
    url: str = ""
    title: str = ""
    scroll_position: int = 0
    active_element: str = ""
    screenshot: bytes = b""
    cookies: List[Dict] = field(default_factory=list)


class BrowserAgent:
    """
    Browser automation agent with human-like mouse movements.

    Can explore websites, fill forms, click elements, scroll, and gather information.
    """

    def __init__(
        self,
        config: BrowserConfig = None,
        human_mouse: HumanMouse = None,
        debug: bool = False
    ):
        self.config = config or BrowserConfig.default()
        self.human_mouse = human_mouse or get_cautious_human_mouse()
        self.debug = debug
        self.browser = None
        self.context = None
        self.page = None
        self.state = BrowserState()
        self._screenshot_count = 0

    async def start(self) -> bool:
        """Start the browser."""
        try:
            from playwright.async_api import async_playwright

            playwright = await async_playwright().start()

            if self.config.headless:
                self.browser = await playwright.chromium.launch(headless=True)
            else:
                self.browser = await playwright.chromium.launch(
                    headless=False,
                    slow_mo=self.config.slow_mo,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-features=IsolateOrigins,site-per-process',
                    ] if self.config.stealth else []
                )

            # Create context with appropriate settings
            context_options = {
                'viewport': {'width': self.config.window_width, 'height': self.config.window_height},
            }

            if self.config.user_agent:
                context_options['user_agent'] = self.config.user_agent

            if not self.config.accept_downloads:
                context_options['accept_downloads'] = False

            self.context = await self.browser.new_context(**context_options)
            self.context.set_default_timeout(30000)

            # Inject stealth scripts
            if self.config.stealth:
                await self._inject_stealth_scripts()

            self.page = await self.context.new_page()
            await self.page.set_viewport_size({
                'width': self.config.window_width,
                'height': self.config.window_height
            })

            # Track state changes
            self.page.on('load', self._on_page_load)
            self.page.on('crash', self._on_page_crash)

            if self.debug:
                print(f"[BrowserAgent] Started - Window: {self.config.window_width}x{self.config.window_height}")

            return True

        except ImportError:
            raise RuntimeError("Playwright not installed. Run: pip install playwright && playwright install chromium")
        except Exception as e:
            if self.debug:
                print(f"[BrowserAgent] Failed to start: {e}")
            return False

    async def _inject_stealth_scripts(self):
        """Inject scripts to avoid detection."""
        stealth_script = """
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        window.chrome = { runtime: {} };
        """
        await self.context.add_init_script(stealth_script)

    async def navigate(self, url: str, wait_until: str = "networkidle") -> bool:
        """Navigate to URL with human-like behavior."""
        try:
            # Simulate human typing URL if no scheme
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            if self.debug:
                print(f"[BrowserAgent] Navigating to: {url}")

            response = await self.page.goto(url, wait_until=wait_until, timeout=30000)

            # Update state
            self.state.url = url
            self.state.title = await self.page.title()

            # Small delay to simulate reading
            await asyncio.sleep(random.uniform(0.5, 1.5))

            return response is not None

        except Exception as e:
            if self.debug:
                print(f"[BrowserAgent] Navigation failed: {e}")
            return False

    async def click_element(
        self,
        selector: str = None,
        xpath: str = None,
        text: str = None,
        index: int = 0,
        human: bool = True
    ) -> bool:
        """Click an element with human-like mouse movement."""
        try:
            element = None

            if selector:
                elements = await self.page.query_selector_all(selector)
                if elements:
                    element = elements[index] if index < len(elements) else elements[0]
            elif xpath:
                elements = await self.page.query_selector_all(f'xpath={xpath}')
                if elements:
                    element = elements[index] if index < len(elements) else elements[0]
            elif text:
                element = await self.page.get_by_text(text, exact=False).first

            if not element:
                if self.debug:
                    print(f"[BrowserAgent] Element not found")
                return False

            box = await element.bounding_box()
            if not box:
                return False

            click_x = box['x'] + box['width'] / 2
            click_y = box['y'] + box['height'] / 2

            if human:
                current_pos = await self._get_current_mouse_position()
                await self._human_move_to(current_pos['x'], current_pos['y'], click_x, click_y)

                # Human-like pause before click
                await asyncio.sleep(random.uniform(0.1, 0.3))

                await self.page.mouse.click(click_x, click_y)
            else:
                await self.page.mouse.click(click_x, click_y)

            # Small delay after click
            await asyncio.sleep(random.uniform(0.2, 0.5))

            if self.debug:
                print(f"[BrowserAgent] Clicked at ({click_x:.0f}, {click_y:.0f})")

            return True

        except Exception as e:
            if self.debug:
                print(f"[BrowserAgent] Click failed: {e}")
            return False

    async def type_text(
        self,
        text: str,
        selector: str = None,
        clear_first: bool = True,
        human: bool = True
    ) -> bool:
        """Type text with human-like timing."""
        try:
            if selector:
                element = await self.page.query_selector(selector)
                if element:
                    await element.click()
                    if clear_first:
                        await element.fill('')

            if human:
                # Type with variable delays
                for char in text:
                    await self.page.keyboard.type(char)
                    delay = random.uniform(0.03, 0.12)
                    if random.random() < 0.05:
                        delay += random.uniform(0.1, 0.3)  # Occasional pause
                    await asyncio.sleep(delay)
            else:
                await self.page.keyboard.type(text)

            if self.debug:
                print(f"[BrowserAgent] Typed: {text[:50]}...")

            return True

        except Exception as e:
            if self.debug:
                print(f"[BrowserAgent] Type failed: {e}")
            return False

    async def scroll(
        self,
        direction: str = "down",
        amount: int = 3,
        human: bool = True
    ) -> bool:
        """Scroll the page with human-like behavior."""
        try:
            for i in range(amount):
                scroll_amount = random.randint(300, 600) if direction == "down" else random.randint(-600, -300)

                if human:
                    # Add slight horizontal drift
                    drift = random.uniform(-50, 50)
                    await self.page.evaluate(f"""
                        window.scrollBy({drift}, {scroll_amount})
                    """)
                    # Variable delay between scrolls
                    await asyncio.sleep(random.uniform(0.1, 0.4))
                else:
                    await self.page.evaluate(f"window.scrollBy(0, {scroll_amount})")

            if self.debug:
                print(f"[BrowserAgent] Scrolled {direction} {amount} times")

            return True

        except Exception as e:
            if self.debug:
                print(f"[BrowserAgent] Scroll failed: {e}")
            return False

    async def hover_element(self, selector: str = None, xpath: str = None) -> bool:
        """Hover over an element."""
        try:
            element = None
            if selector:
                element = await self.page.query_selector(selector)
            elif xpath:
                element = await self.page.query_selector(f'xpath={xpath}')

            if not element:
                return False

            box = await element.bounding_box()
            if not box:
                return False

            x = box['x'] + box['width'] / 2
            y = box['y'] + box['height'] / 2

            current_pos = await self._get_current_mouse_position()
            await self._human_move_to(current_pos['x'], current_pos['y'], x, y)

            # Human-like hover duration
            await asyncio.sleep(random.uniform(0.3, 0.8))

            return True

        except Exception as e:
            if self.debug:
                print(f"[BrowserAgent] Hover failed: {e}")
            return False

    async def take_screenshot(self, full_page: bool = False) -> bytes:
        """Take a screenshot of the current page."""
        try:
            if full_page:
                return await self.page.screenshot(full_page=True)
            else:
                return await self.page.screenshot()

        except Exception as e:
            if self.debug:
                print(f"[BrowserAgent] Screenshot failed: {e}")
            return b""

    async def save_screenshot(self, path: str = None) -> str:
        """Save screenshot to file."""
        screenshot = await self.take_screenshot()
        if not screenshot:
            return ""

        if not path:
            self._screenshot_count += 1
            path = f"screenshot_{self._screenshot_count}.png"

        with open(path, 'wb') as f:
            f.write(screenshot)

        return path

    async def get_page_content(self) -> str:
        """Get the full page content."""
        try:
            return await self.page.content()
        except Exception:
            return ""

    async def get_text_content(self, selector: str = None) -> str:
        """Get text content from page or element."""
        try:
            if selector:
                element = await self.page.query_selector(selector)
                if element:
                    return await element.inner_text()
            return await self.page.inner_text('body')
        except Exception:
            return ""

    async def find_elements(self, pattern: str, case_sensitive: bool = False) -> List[Dict]:
        """Find elements matching a pattern (text or attribute)."""
        try:
            # Use JavaScript to find elements
            js = f"""
            (function() {{
                const pattern = /{re.escape(pattern)}/{'i' if not case_sensitive else ''};
                const results = [];
                const allElements = document.querySelectorAll('a, button, input, span, div, p, h1, h2, h3, h4, h5, h6');

                allElements.forEach((el, index) => {{
                    const text = el.textContent || '';
                    const href = el.href || '';
                    const title = el.title || '';
                    const alt = el.alt || '';

                    if (pattern.test(text) || pattern.test(href) || pattern.test(title) || pattern.test(alt)) {{
                        const box = el.getBoundingClientRect();
                        results.push({{
                            tag: el.tagName.toLowerCase(),
                            text: text.trim().substring(0, 200),
                            href: href,
                            x: box.x,
                            y: box.y,
                            width: box.width,
                            height: box.height,
                            index: index
                        }});
                    }}
                }});

                return results;
            }})()
            """

            results = await self.page.evaluate(js)
            return results if results else []

        except Exception as e:
            if self.debug:
                print(f"[BrowserAgent] Find failed: {e}")
            return []

    async def search_google(self, query: str) -> bool:
        """Search Google with the query."""
        query_encoded = requests.utils.quote(query)
        return await self.navigate(f"https://www.google.com/search?q={query_encoded}")

    async def search(self, search_engine: str, query: str) -> bool:
        """Search using specified engine."""
        query_encoded = requests.utils.quote(query)

        engines = {
            'google': 'https://www.google.com/search?q=',
            'duckduckgo': 'https://duckduckgo.com/?q=',
            'bing': 'https://www.bing.com/search?q=',
            'brave': 'https://search.brave.com/search?q='
        }

        url = engines.get(search_engine.lower(), engines['google']) + query_encoded
        return await self.navigate(url)

    async def fill_form(self, form_data: Dict[str, str]) -> bool:
        """Fill a form with data."""
        try:
            for field_name, value in form_data.items():
                # Try different selectors
                selectors = [
                    f'[name="{field_name}"]',
                    f'#id_{field_name}',
                    f'[id="{field_name}"]',
                    f'input[placeholder*="{field_name}" i]',
                    f'text="{field_name}"'
                ]

                element = None
                for selector in selectors:
                    element = await self.page.query_selector(selector)
                    if element:
                        break

                if element:
                    await element.click()
                    await element.fill(value)
                    # Variable typing speed
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                else:
                    if self.debug:
                        print(f"[BrowserAgent] Field '{field_name}' not found")

            return True

        except Exception as e:
            if self.debug:
                print(f"[BrowserAgent] Form fill failed: {e}")
            return False

    async def submit_form(self, selector: str = "form") -> bool:
        """Submit a form."""
        try:
            form = await self.page.query_selector(selector)
            if form:
                await form.evaluate('form => form.submit()')
                return True

            # Try finding submit button
            return await self.click_element('button[type="submit"]') or \
                   await self.click_element('input[type="submit"]')

        except Exception as e:
            if self.debug:
                print(f"[BrowserAgent] Submit failed: {e}")
            return False

    async def wait_for_element(self, selector: str, timeout: int = 30) -> bool:
        """Wait for an element to appear."""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout * 1000)
            return True
        except Exception:
            return False

    async def wait_for_navigation(self, timeout: int = 30) -> bool:
        """Wait for page navigation."""
        try:
            await self.page.wait_for_load_state('networkidle', timeout=timeout * 1000)
            return True
        except Exception:
            return False

    async def get_cookies(self) -> List[Dict]:
        """Get current page cookies."""
        try:
            return await self.context.cookies()
        except Exception:
            return []

    async def set_cookies(self, cookies: List[Dict]):
        """Set cookies."""
        try:
            await self.context.add_cookies(cookies)
        except Exception:
            pass

    async def get_local_storage(self, key: str = None) -> Dict:
        """Get localStorage data."""
        if key:
            result = await self.page.evaluate(f"return localStorage.getItem('{key}')")
            return result
        else:
            return await self.page.evaluate("return Object.assign({}, localStorage)")

    async def execute_script(self, script: str) -> Any:
        """Execute JavaScript on the page."""
        try:
            return await self.page.evaluate(script)
        except Exception as e:
            if self.debug:
                print(f"[BrowserAgent] Script failed: {e}")
            return None

    # Helper methods
    async def _get_current_mouse_position(self) -> Dict[str, int]:
        """Get current mouse position."""
        return await self.page.evaluate("""
            () => ({
                x: window.mouseX || 0,
                y: window.mouseY || 0
            })
        """)

    async def _human_move_to(self, from_x: int, from_y: int, to_x: int, to_y: int):
        """Move mouse with human-like behavior."""
        # Convert async to sync for the human mouse
        self.human_mouse.move_to(
            (from_x, from_y),
            (to_x, to_y),
            on_move=lambda x, y: asyncio.create_task(
                self.page.mouse.move(x, y)
            )
        )
        # Actually move
        await self.page.mouse.move(int(to_x), int(to_y))

    async def _on_page_load(self, page):
        """Handle page load event."""
        self.state.url = page.url
        self.state.title = await page.title()
        if self.debug:
            print(f"[BrowserAgent] Page loaded: {self.state.title}")

    async def _on_page_crash(self):
        """Handle page crash."""
        if self.debug:
            print("[BrowserAgent] Page crashed!")

    async def close(self):
        """Close the browser."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.debug:
            print("[BrowserAgent] Browser closed")

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class BrowserSurvey(BrowserAgent):
    """
    Specialized browser agent for filling out surveys and forms.
    """

    async def fill_survey(self, answers: Dict[str, Any]) -> Dict[str, bool]:
        """Fill a survey with answers."""
        results = {}

        for question, answer in answers.items():
            try:
                # Try to find the question/field
                found = await self.find_elements(question)

                if found:
                    element_info = found[0]
                    x = element_info['x'] + element_info['width'] / 2
                    y = element_info['y'] + element_info['height'] / 2

                    await self._human_move_to(0, 0, x, y)
                    await asyncio.sleep(0.3)
                    await self.page.mouse.click(x, y)

                    if isinstance(answer, str):
                        await self.type_text(answer)
                    elif isinstance(answer, bool):
                        # Check/uncheck
                        await self.page.keyboard.press('Space')
                    elif isinstance(answer, int):
                        # Option selection
                        for _ in range(answer):
                            await self.page.keyboard.press('ArrowDown')
                        await self.page.keyboard.press('Enter')

                    results[question] = True
                else:
                    results[question] = False

            except Exception as e:
                results[question] = False
                if self.debug:
                    print(f"Failed to answer: {question} - {e}")

        return results


# Utility functions
async def create_browser_agent(
    headless: bool = False,
    slow: bool = True,
    debug: bool = False
) -> BrowserAgent:
    """Create and start a browser agent."""
    config = BrowserConfig(
        headless=headless,
        stealth=True,
        window_width=1280,
        window_height=800
    )

    mouse = get_cautious_human_mouse() if slow else get_human_mouse()

    agent = BrowserAgent(config=config, human_mouse=mouse, debug=debug)
    await agent.start()
    return agent