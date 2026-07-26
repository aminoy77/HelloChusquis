"""
Browser Controller Agent — v2
Controls a browser instance for web automation.
Anti-detection, human-like mouse, persistent contexts, cookies, network intercept.
"""

import asyncio
import json
import logging
import os
import random
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.human_mouse import (
    HumanMouse,
    get_human_mouse,
    get_cautious_human_mouse,
)

logger = logging.getLogger("browser_agent")


@dataclass
class BrowserConfig:
    """Configuration for browser automation."""
    headless: bool = False
    window_width: int = 1280
    window_height: int = 800
    user_agent: Optional[str] = None
    locale: str = "en-US"
    timezone_id: str = "America/New_York"
    geolocation: Optional[Dict[str, float]] = None
    accept_downloads: bool = False
    download_path: Optional[str] = None
    slow_mo: int = 50
    stealth: bool = True
    proxy: Optional[Dict[str, str]] = None
    ignore_https_errors: bool = False
    viewport_width: int = 1280
    viewport_height: int = 800
    device_scale_factor: float = 1.0
    has_touch: bool = False
    is_mobile: bool = False
    record_video: bool = False
    record_har: bool = False
    trace: bool = False
    navigation_timeout: int = 30000
    action_timeout: int = 15000

    @classmethod
    def default(cls):
        return cls()

    @classmethod
    def headless_default(cls):
        return cls(headless=True, slow_mo=0)

    @classmethod
    def undetected(cls):
        """Config optimizada para evitar detección como bot."""
        return cls(
            headless=False,
            stealth=True,
            window_width=1920,
            window_height=1080,
            slow_mo=20,
            locale="en-US",
            timezone_id="America/New_York",
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
        )


@dataclass
class BrowserState:
    """Current state of the browser."""
    url: str = ""
    title: str = ""
    scroll_position: int = 0
    active_element: str = ""
    cookies_count: int = 0
    local_storage_count: int = 0
    performance_metrics: Dict = field(default_factory=dict)
    is_connected: bool = False
    last_action: str = ""
    last_action_time: Optional[float] = None
    errors_since_last_health: int = 0


class BrowserAgent:
    """
    Browser automation agent with:
    - Anti-detection (stealth mode)
    - Human-like mouse movements
    - Cookie/session persistence
    - Popup & dialog handling
    - Network request interception
    - Health checks & auto-recovery
    - Screenshot & tracing
    """

    def __init__(
        self,
        config: BrowserConfig = None,
        human_mouse: HumanMouse = None,
        debug: bool = False,
    ):
        self.config = config or BrowserConfig.default()
        self.human_mouse = human_mouse or get_cautious_human_mouse()
        self.debug = debug

        if debug:
            logger.setLevel(logging.DEBUG)

        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.state = BrowserState()
        self._screenshot_count = 0
        self._session_dir = None
        self._pending_dialogs = asyncio.Queue()
        self._route_handlers = []
        self._health_check_interval = 10
        self._last_health_check = 0.0

    async def start(self) -> bool:
        """Start the browser with full configuration."""
        try:
            from playwright.async_api import async_playwright

            self.playwright = await async_playwright().start()

            launch_args = [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
            ]

            if self.config.stealth:
                stealth_args = [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-web-security',
                    '--disable-features=ChromeWhatsNewUI',
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-background-networking',
                    '--disable-sync',
                    '--disable-translate',
                    '--disable-features=Translate',
                    '--hide-scrollbars',
                    '--mute-audio',
                    '--disable-component-update',
                    '--disable-background-timer-throttling',
                ]
                launch_args.extend(stealth_args)

            launch_kwargs = {
                'headless': self.config.headless,
                'args': launch_args,
            }

            if self.config.slow_mo > 0 and not self.config.headless:
                launch_kwargs['slow_mo'] = self.config.slow_mo

            if self.config.proxy:
                launch_kwargs['proxy'] = self.config.proxy

            if self.config.ignore_https_errors:
                launch_kwargs['ignore_https_errors'] = True

            self.browser = await self.playwright.chromium.launch(**launch_kwargs)

            # Create context with realistic browser fingerprint
            await self._create_context()

            self.page = await self.context.new_page()
            await self.page.set_viewport_size({
                'width': self.config.viewport_width,
                'height': self.config.viewport_height,
            })

            # Stealth: inject anti-detection scripts
            if self.config.stealth:
                await self._inject_full_stealth()

            # Set up event handlers
            self.page.on('load', self._on_page_load)
            self.page.on('crash', self._on_page_crash)
            self.page.on('dialog', self._on_dialog)
            self.page.on('popup', self._on_popup)
            self.page.on('console', self._on_console)

            # Set default timeouts
            self.page.set_default_timeout(self.config.action_timeout)
            self.context.set_default_timeout(self.config.navigation_timeout)

            self.state.is_connected = True
            self.state.last_action_time = time.time()

            if self.debug:
                logger.info(
                    "BrowserAgent ready | %dx%d | stealth=%s | headless=%s",
                    self.config.viewport_width,
                    self.config.viewport_height,
                    self.config.stealth,
                    self.config.headless,
                )

            return True

        except ImportError:
            raise RuntimeError(
                "Playwright not installed. Run: pip install playwright && playwright install chromium"
            )
        except Exception as e:
            logger.error("BrowserAgent start failed: %s", e, exc_info=self.debug)
            return False

    async def _create_context(self):
        """Create a browser context with realistic fingerprint."""
        context_options = {
            'viewport': {
                'width': self.config.viewport_width,
                'height': self.config.viewport_height,
            },
            'locale': self.config.locale,
            'timezone_id': self.config.timezone_id,
            'device_scale_factor': self.config.device_scale_factor,
            'has_touch': self.config.has_touch,
            'is_mobile': self.config.is_mobile,
            'ignore_https_errors': self.config.ignore_https_errors,
        }

        if self.config.user_agent:
            context_options['user_agent'] = self.config.user_agent

        if self.config.geolocation:
            context_options['geolocation'] = self.config.geolocation
            context_options['permissions'] = ['geolocation']

        if self.config.accept_downloads:
            context_options['accept_downloads'] = True
            if self.config.download_path:
                Path(self.config.download_path).mkdir(parents=True, exist_ok=True)

        if self.config.proxy:
            context_options['proxy'] = self.config.proxy

        if self.config.record_video:
            video_dir = Path("recordings")
            video_dir.mkdir(exist_ok=True)
            context_options['record_video_dir'] = str(video_dir)
            context_options['record_video_size'] = {
                'width': self.config.viewport_width,
                'height': self.config.viewport_height,
            }

        if self.config.record_har:
            har_path = f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}.har"

        self.context = await self.browser.new_context(**context_options)

    async def _inject_full_stealth(self):
        """Inject comprehensive anti-detection scripts."""
        stealth_js = """
        // Override webdriver
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });

        // Override plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                { name: 'Native Client', filename: 'internal-nacl-plugin' },
            ],
        });

        // Override languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en', 'es'],
        });

        // Override hardwareConcurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8,
        });

        // Override deviceMemory
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 8,
        });

        // Override platform
        Object.defineProperty(navigator, 'platform', {
            get: () => 'MacIntel',
        });

        // Chrome runtime
        window.chrome = {
            runtime: {
                onMessage: { addListener: () => {} },
                onConnect: { addListener: () => {} },
                onInstalled: { addListener: () => {} },
            },
            loadTimes: () => {},
            csi: () => {},
            app: { isInstalled: false },
        };

        // Permissions
        const originalQuery = navigator.permissions.query;
        navigator.permissions.query = (params) => (
            params.name === 'notifications'
                ? Promise.resolve({ state: Notification.permission })
                : originalQuery(params)
        );

        // WebGL vendor
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(p) {
            if (p === 37445) return 'Intel Inc.';
            if (p === 37446) return 'Intel Iris OpenGL Engine';
            return getParameter.call(this, p);
        };

        // Override toString
        const makeFakeProto = () => ({
            toString: () => '[object Chrome]',
            [Symbol.toStringTag]: 'Chrome',
        });
        navigator.constructor.prototype.toString = () => '[object Navigator]';
        """
        await self.context.add_init_script(stealth_js)

    async def health_check(self) -> bool:
        """Check if browser is still alive and responsive."""
        now = time.time()
        if now - self._last_health_check < self._health_check_interval:
            return self.state.is_connected

        self._last_health_check = now

        if not self.page or not self.state.is_connected:
            return False

        try:
            await self.page.evaluate("1 + 1")
            self.state.errors_since_last_health = 0
            return True
        except Exception as e:
            self.state.errors_since_last_health += 1
            logger.warning("Health check failed (%d): %s", self.state.errors_since_last_health, e)

            if self.state.errors_since_last_health >= 3:
                logger.error("Browser unresponsive. Attempting recovery...")
                await self.recover()
                return False

            return False

    async def recover(self):
        """Attempt to recover from browser crash/freeze."""
        logger.info("Attempting browser recovery...")
        try:
            await self.close()
        except Exception:
            pass

        self.state = BrowserState()
        self._screenshot_count = 0
        success = await self.start()
        if success:
            logger.info("Browser recovered successfully")
        else:
            logger.error("Browser recovery failed")
        return success

    # ─── NAVIGATION ────────────────────────────────────────────────

    async def navigate(
        self,
        url: str,
        wait_until: str = "networkidle",
        referer: str = None,
    ) -> bool:
        """Navigate to URL with retries and timeout."""
        if not await self.health_check():
            return False

        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            if self.debug:
                logger.info("→ navigate: %s", url)

            goto_kwargs = {
                'url': url,
                'wait_until': wait_until,
                'timeout': self.config.navigation_timeout,
            }
            if referer:
                goto_kwargs['referer'] = referer

            response = await self.page.goto(**goto_kwargs)

            self.state.url = url
            self.state.title = (await self.page.title()) or ""
            self.state.last_action = "navigate"
            self.state.last_action_time = time.time()

            await asyncio.sleep(random.uniform(0.3, 0.8))

            return response is not None and response.ok

        except Exception as e:
            logger.error("Navigation failed: %s", e)
            return False

    async def go_back(self) -> bool:
        """Navigate back in history."""
        try:
            await self.page.go_back(wait_until='networkidle')
            self.state.url = self.page.url
            self.state.title = await self.page.title() or ""
            return True
        except Exception as e:
            logger.error("go_back failed: %s", e)
            return False

    async def go_forward(self) -> bool:
        """Navigate forward in history."""
        try:
            await self.page.go_forward(wait_until='networkidle')
            self.state.url = self.page.url
            self.state.title = await self.page.title() or ""
            return True
        except Exception as e:
            logger.error("go_forward failed: %s", e)
            return False

    async def reload(self) -> bool:
        """Reload current page."""
        try:
            await self.page.reload(wait_until='networkidle')
            self.state.title = await self.page.title() or ""
            return True
        except Exception as e:
            logger.error("reload failed: %s", e)
            return False

    # ─── CLICKING ──────────────────────────────────────────────────

    async def click_element(
        self,
        selector: str = None,
        xpath: str = None,
        text: str = None,
        index: int = 0,
        human: bool = True,
        timeout: int = None,
    ) -> bool:
        """Click an element with human-like mouse movement."""
        if not await self.health_check():
            return False

        try:
            locator = None
            if selector:
                locator = self.page.locator(selector)
            elif xpath:
                locator = self.page.locator(f'xpath={xpath}')
            elif text:
                locator = self.page.get_by_text(text, exact=False)

            if not locator:
                if self.debug:
                    logger.warning("click_element: no locator provided")
                return False

            timeout_ms = (timeout or self.config.action_timeout)
            element = locator.nth(index)

            # Wait for element to be visible
            try:
                await element.wait_for(state='visible', timeout=timeout_ms)
            except Exception:
                if self.debug:
                    logger.warning("click_element: element not visible")
                return False

            box = await element.bounding_box()
            if not box:
                if self.debug:
                    logger.warning("click_element: bounding box not found")
                return False

            click_x = box['x'] + box['width'] / 2 + random.uniform(-2, 2)
            click_y = box['y'] + box['height'] / 2 + random.uniform(-2, 2)

            if human:
                current_pos = await self._get_current_mouse_position()
                await self._human_move_to(
                    current_pos['x'], current_pos['y'], click_x, click_y
                )
                await asyncio.sleep(random.uniform(0.05, 0.15))
                await self.page.mouse.click(click_x, click_y)
                await asyncio.sleep(random.uniform(0.1, 0.3))
            else:
                await element.click(timeout=timeout_ms)

            self.state.last_action = "click"
            self.state.last_action_time = time.time()

            if self.debug:
                logger.info("→ click (%d, %d) on %s", click_x, click_y, selector or text or xpath)

            return True

        except Exception as e:
            logger.error("Click failed: %s", e)
            return False

    async def double_click(
        self, selector: str = None, xpath: str = None, text: str = None
    ) -> bool:
        """Double-click an element."""
        try:
            if selector:
                await self.page.locator(selector).dblclick()
            elif xpath:
                await self.page.locator(f'xpath={xpath}').dblclick()
            elif text:
                await self.page.get_by_text(text, exact=False).dblclick()
            else:
                return False
            return True
        except Exception as e:
            logger.error("Double click failed: %s", e)
            return False

    async def right_click(
        self, selector: str = None, xpath: str = None, text: str = None
    ) -> bool:
        """Right-click an element."""
        try:
            if selector:
                await self.page.locator(selector).click(button='right')
            elif xpath:
                await self.page.locator(f'xpath={xpath}').click(button='right')
            elif text:
                await self.page.get_by_text(text, exact=False).click(button='right')
            else:
                return False
            return True
        except Exception as e:
            logger.error("Right click failed: %s", e)
            return False

    async def hover_element(
        self, selector: str = None, xpath: str = None, text: str = None
    ) -> bool:
        """Hover over an element."""
        try:
            locator = None
            if selector:
                locator = self.page.locator(selector)
            elif xpath:
                locator = self.page.locator(f'xpath={xpath}')
            elif text:
                locator = self.page.get_by_text(text, exact=False)

            if not locator:
                return False

            box = await locator.bounding_box()
            if not box:
                return False

            x = box['x'] + box['width'] / 2
            y = box['y'] + box['height'] / 2

            current_pos = await self._get_current_mouse_position()
            await self._human_move_to(current_pos['x'], current_pos['y'], x, y)
            await asyncio.sleep(random.uniform(0.3, 0.8))

            return True
        except Exception as e:
            logger.error("Hover failed: %s", e)
            return False

    # ─── TYPING ────────────────────────────────────────────────────

    async def type_text(
        self,
        text: str,
        selector: str = None,
        clear_first: bool = True,
        human: bool = True,
    ) -> bool:
        """Type text with human-like timing."""
        try:
            if selector:
                element = self.page.locator(selector)
                try:
                    await element.wait_for(state='visible', timeout=self.config.action_timeout)
                except Exception:
                    return False
                await element.click()
                if clear_first:
                    await element.fill('')

            if human:
                for char in text:
                    await self.page.keyboard.type(char)
                    delay = random.uniform(0.03, 0.12)
                    if random.random() < 0.05:
                        delay += random.uniform(0.1, 0.3)
                    await asyncio.sleep(delay)
            else:
                await self.page.keyboard.type(text)

            self.state.last_action = "type"
            self.state.last_action_time = time.time()

            if self.debug:
                logger.info("→ typed: %s...", text[:50])

            return True
        except Exception as e:
            logger.error("Type failed: %s", e)
            return False

    async def press_key(self, key: str):
        """Press a keyboard key (Enter, Tab, Escape, ArrowDown, etc)."""
        try:
            await self.page.keyboard.press(key)
            return True
        except Exception:
            return False

    # ─── SCROLLING ─────────────────────────────────────────────────

    async def scroll(
        self,
        direction: str = "down",
        amount: int = 3,
        human: bool = True,
    ) -> bool:
        """Scroll the page with human-like behavior."""
        if not await self.health_check():
            return False

        try:
            for i in range(amount):
                if direction == "down":
                    scroll_amount = random.randint(300, 600)
                else:
                    scroll_amount = random.randint(-600, -300)

                if human:
                    drift = random.uniform(-50, 50)
                    await self.page.evaluate(
                        f"window.scrollBy({drift}, {scroll_amount})"
                    )
                    await asyncio.sleep(random.uniform(0.1, 0.4))
                else:
                    await self.page.evaluate(
                        f"window.scrollBy(0, {scroll_amount})"
                    )

            self.state.last_action = "scroll"
            return True
        except Exception as e:
            logger.error("Scroll failed: %s", e)
            return False

    async def scroll_to_element(self, selector: str) -> bool:
        """Scroll until element is visible."""
        try:
            await self.page.locator(selector).scroll_into_view_if_needed()
            await asyncio.sleep(0.3)
            return True
        except Exception:
            return False

    async def scroll_to_bottom(self, smooth: bool = True) -> bool:
        """Scroll to bottom of page."""
        try:
            behavior = "smooth" if smooth else "auto"
            await self.page.evaluate(
                f"window.scrollTo({{ top: document.body.scrollHeight, behavior: '{behavior}' }})"
            )
            await asyncio.sleep(0.5)
            return True
        except Exception:
            return False

    async def scroll_to_top(self) -> bool:
        """Scroll to top of page."""
        try:
            await self.page.evaluate("window.scrollTo({ top: 0, behavior: 'smooth' })")
            await asyncio.sleep(0.3)
            return True
        except Exception:
            return False

    # ─── SCREENSHOTS ───────────────────────────────────────────────

    async def take_screenshot(self, full_page: bool = False, quality: int = 80) -> bytes:
        """Take a screenshot of the current page."""
        try:
            opts = {'type': 'jpeg', 'quality': quality}
            if full_page:
                opts['full_page'] = True
            return await self.page.screenshot(**opts)
        except Exception as e:
            logger.error("Screenshot failed: %s", e)
            return b""

    async def save_screenshot(
        self, path: str = None, full_page: bool = False
    ) -> Optional[str]:
        """Save screenshot to file."""
        screenshot = await self.take_screenshot(full_page=full_page)
        if not screenshot:
            return None

        if not path:
            self._screenshot_count += 1
            path = f"screenshot_{self._screenshot_count}.png"

        with open(path, 'wb') as f:
            f.write(screenshot)

        return path

    async def element_screenshot(self, selector: str, path: str = None) -> Optional[str]:
        """Take screenshot of a specific element."""
        try:
            element = self.page.locator(selector)
            if not path:
                self._screenshot_count += 1
                path = f"element_screenshot_{self._screenshot_count}.png"
            await element.screenshot(path=path)
            return path
        except Exception:
            return None

    # ─── CONTENT EXTRACTION ───────────────────────────────────────

    async def get_page_content(self) -> str:
        """Get the full page HTML content."""
        try:
            return await self.page.content()
        except Exception:
            return ""

    async def get_text_content(self, selector: str = None) -> str:
        """Get text content from page or specific element."""
        try:
            if selector:
                element = self.page.locator(selector)
                return await element.inner_text()
            return await self.page.inner_text('body')
        except Exception:
            return ""

    async def get_visible_text(self) -> str:
        """Get only visible text content."""
        try:
            return await self.page.evaluate("""
                () => document.body.innerText
            """)
        except Exception:
            return ""

    async def get_html(self, selector: str = None) -> str:
        """Get inner HTML of page or element."""
        try:
            if selector:
                return await self.page.locator(selector).inner_html()
            return await self.page.content()
        except Exception:
            return ""

    async def get_attribute(self, selector: str, attr: str) -> Optional[str]:
        """Get attribute value of an element."""
        try:
            return await self.page.locator(selector).get_attribute(attr)
        except Exception:
            return None

    async def get_value(self, selector: str) -> Optional[str]:
        """Get input value of an element."""
        try:
            return await self.page.locator(selector).input_value()
        except Exception:
            return None

    async def get_url(self) -> str:
        """Get current page URL."""
        try:
            return self.page.url
        except Exception:
            return self.state.url

    async def get_title(self) -> str:
        """Get current page title."""
        try:
            return await self.page.title() or ""
        except Exception:
            return self.state.title

    # ─── FINDING ELEMENTS ─────────────────────────────────────────

    async def find_elements(
        self, pattern: str, case_sensitive: bool = False, max_results: int = 50
    ) -> List[Dict]:
        """Find elements matching a pattern (text or attribute)."""
        try:
            flags = '' if case_sensitive else 'i'
            escaped = re.escape(pattern)

            js = f"""
            (function() {{
                const pattern = /{escaped}/{flags};
                const results = [];
                const selectors = [
                    'a', 'button', 'input', 'span', 'div', 'p',
                    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                    'label', 'textarea', 'select', 'li', 'td', 'th',
                    'img', 'svg', 'path',
                ];
                const elements = document.querySelectorAll(selectors.join(', '));

                elements.forEach((el, index) => {{
                    const text = el.textContent || '';
                    const href = el.href || '';
                    const title = el.title || '';
                    const alt = el.alt || '';
                    const ariaLabel = el.getAttribute('aria-label') || '';
                    const placeholder = el.placeholder || '';
                    const value = el.value || '';

                    if (
                        pattern.test(text) ||
                        pattern.test(href) ||
                        pattern.test(title) ||
                        pattern.test(alt) ||
                        pattern.test(ariaLabel) ||
                        pattern.test(placeholder) ||
                        pattern.test(value)
                    ) {{
                        const box = el.getBoundingClientRect();
                        const computed = window.getComputedStyle(el);
                        results.push({{
                            tag: el.tagName.toLowerCase(),
                            id: el.id || '',
                            class: el.className || '',
                            text: text.trim().substring(0, 200),
                            href: href,
                            alt: alt,
                            ariaLabel: ariaLabel,
                            placeholder: placeholder,
                            visible: computed.display !== 'none' && computed.visibility !== 'hidden',
                            x: box.x,
                            y: box.y,
                            width: box.width,
                            height: box.height,
                            index: index,
                        }});
                    }}
                }});

                return results.slice(0, {max_results});
            }})()
            """

            results = await self.page.evaluate(js)
            return results if results else []

        except Exception as e:
            logger.error("Find elements failed: %s", e)
            return []

    async def wait_for_element(
        self, selector: str, timeout: int = 30, state: str = 'visible'
    ) -> bool:
        """Wait for an element to appear with specific state."""
        try:
            await self.page.wait_for_selector(
                selector, timeout=timeout * 1000, state=state
            )
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

    async def wait_for_timeout(self, ms: int = 1000):
        """Wait for a specified timeout."""
        await asyncio.sleep(ms / 1000)

    async def wait_for_function(
        self, fn: str, timeout: int = 30, arg: Any = None
    ) -> bool:
        """Wait for a JavaScript function to return true."""
        try:
            await self.page.wait_for_function(fn, timeout=timeout * 1000, arg=arg)
            return True
        except Exception:
            return False

    # ─── FORMS ─────────────────────────────────────────────────────

    async def fill_form(self, form_data: Dict[str, str]) -> int:
        """Fill a form with data. Returns number of fields filled."""
        filled = 0
        try:
            for field_name, value in form_data.items():
                selectors = [
                    f'[name="{field_name}"]',
                    f'#id_{field_name}',
                    f'[id="{field_name}"]',
                    f'input[placeholder*="{field_name}" i]',
                    f'textarea[placeholder*="{field_name}" i]',
                    f'[aria-label*="{field_name}" i]',
                ]

                element = None
                found_selector = None
                for s in selectors:
                    try:
                        el = self.page.locator(s)
                        if await el.count() > 0:
                            element = el
                            found_selector = s
                            break
                    except Exception:
                        pass

                if element:
                    try:
                        await element.wait_for(state='visible', timeout=5000)
                        await element.click()
                        await element.fill(value)
                        await asyncio.sleep(random.uniform(0.1, 0.3))
                        filled += 1
                    except Exception:
                        pass

            return filled
        except Exception:
            return filled

    async def select_option(
        self, selector: str, value: str = None, label: str = None, index: int = None
    ) -> bool:
        """Select an option in a select element."""
        try:
            kwargs = {}
            if value:
                kwargs['value'] = value
            elif label:
                kwargs['label'] = label
            elif index is not None:
                kwargs['index'] = index
            await self.page.locator(selector).select_option(**kwargs)
            return True
        except Exception:
            return False

    async def submit_form(self, selector: str = "form") -> bool:
        """Submit a form."""
        try:
            form = self.page.locator(selector)
            if await form.count() > 0:
                await form.evaluate('form => form.submit()')
                return True
            return bool(
                await self.click_element('button[type="submit"]')
                or await self.click_element('input[type="submit"]')
            )
        except Exception as e:
            logger.error("Submit failed: %s", e)
            return False

    async def upload_file(self, selector: str, file_path: str) -> bool:
        """Upload a file using file input."""
        try:
            await self.page.locator(selector).set_input_files(file_path)
            return True
        except Exception:
            return False

    async def check_checkbox(self, selector: str, checked: bool = True) -> bool:
        """Check or uncheck a checkbox."""
        try:
            await self.page.locator(selector).set_checked(checked)
            return True
        except Exception:
            return False

    # ─── JAVASCRIPT ────────────────────────────────────────────────

    async def execute_script(self, script: str) -> Any:
        """Execute JavaScript on the page."""
        try:
            return await self.page.evaluate(script)
        except Exception as e:
            logger.error("Script execution failed: %s", e)
            return None

    async def execute_async_script(self, script: str, *args) -> Any:
        """Execute async JavaScript on the page."""
        try:
            return await self.page.evaluate_handle(script, *args)
        except Exception:
            return None

    # ─── SEARCH ────────────────────────────────────────────────────

    async def search(self, query: str, engine: str = 'google') -> bool:
        """Search using specified search engine."""
        query_encoded = __import__('urllib.parse').parse.quote(query)

        engines = {
            'google': 'https://www.google.com/search?q=',
            'duckduckgo': 'https://duckduckgo.com/?q=',
            'bing': 'https://www.bing.com/search?q=',
            'brave': 'https://search.brave.com/search?q=',
            'yahoo': 'https://search.yahoo.com/search?p=',
            'ecosia': 'https://www.ecosia.org/search?q=',
        }

        url = engines.get(engine.lower(), engines['google']) + query_encoded
        return await self.navigate(url)

    # ─── COOKIES & STORAGE ─────────────────────────────────────────

    async def get_cookies(self) -> List[Dict]:
        """Get all cookies from the current context."""
        try:
            cookies = await self.context.cookies()
            self.state.cookies_count = len(cookies)
            return cookies
        except Exception:
            return []

    async def set_cookies(self, cookies: List[Dict]):
        """Set cookies in the current context."""
        try:
            await self.context.add_cookies(cookies)
        except Exception:
            pass

    async def clear_cookies(self):
        """Clear all cookies."""
        try:
            await self.context.clear_cookies()
            self.state.cookies_count = 0
        except Exception:
            pass

    async def get_local_storage(self) -> Dict[str, str]:
        """Get all localStorage items."""
        try:
            return await self.page.evaluate("() => JSON.stringify(window.localStorage)")
        except Exception:
            return {}

    async def set_local_storage(self, key: str, value: str):
        """Set a localStorage item."""
        try:
            await self.page.evaluate(f"window.localStorage.setItem('{key}', '{value}')")
        except Exception:
            pass

    async def clear_local_storage(self):
        """Clear all localStorage."""
        try:
            await self.page.evaluate("window.localStorage.clear()")
        except Exception:
            pass

    # ─── NETWORK ───────────────────────────────────────────────────

    async def intercept_request(
        self,
        url_pattern: str = None,
        handler=None,
    ):
        """Intercept and handle network requests."""
        try:
            async def default_handler(route):
                if url_pattern and url_pattern in route.request.url:
                    await route.abort()
                else:
                    await route.continue_()

            await self.context.route(
                url_pattern or '**/*',
                handler or default_handler,
            )
        except Exception:
            pass

    async def block_resources(self, patterns: List[str] = None):
        """Block resources matching patterns (images, fonts, etc)."""
        if patterns is None:
            patterns = []
        block_patterns = patterns or [
            '*.png', '*.jpg', '*.jpeg', '*.gif', '*.svg',
            '*.woff', '*.woff2', '*.ttf', '*.eot',
        ]
        for pattern in block_patterns:
            await self.context.route(pattern, lambda route: route.abort())

    async def unblock_all_resources(self):
        """Remove all route handlers."""
        try:
            await self.context.unroute('**/*')
        except Exception:
            pass

    # ─── PAGES & TABS ──────────────────────────────────────────────

    async def get_pages(self) -> List[Any]:
        """Get all open pages/tabs."""
        try:
            return self.context.pages
        except Exception:
            return []

    async def switch_to_page(self, index: int = 0) -> bool:
        """Switch to a specific tab by index."""
        try:
            pages = self.context.pages
            if 0 <= index < len(pages):
                self.page = pages[index]
                await self.page.bring_to_front()
                return True
            return False
        except Exception:
            return False

    async def open_new_tab(self, url: str = None) -> bool:
        """Open a new tab, optionally navigating to a URL."""
        try:
            new_page = await self.context.new_page()
            self.page = new_page
            if url:
                await self.navigate(url)
            return True
        except Exception:
            return False

    async def close_current_tab(self) -> bool:
        """Close the current tab and switch to another if available."""
        try:
            pages = self.context.pages
            if len(pages) <= 1:
                return False
            current_index = pages.index(self.page)
            await self.page.close()
            pages = self.context.pages
            new_index = min(current_index, len(pages) - 1)
            self.page = pages[new_index]
            await self.page.bring_to_front()
            return True
        except Exception:
            return False

    async def get_page_count(self) -> int:
        """Get number of open pages/tabs."""
        try:
            return len(self.context.pages)
        except Exception:
            return 0

    async def close_other_tabs(self):
        """Close all tabs except the current one."""
        try:
            for page in self.context.pages:
                if page != self.page:
                    await page.close()
            return True
        except Exception:
            return False

    # ─── DIALOGS ───────────────────────────────────────────────────

    async def _on_dialog(self, dialog):
        """Handle browser dialogs (alert, confirm, prompt)."""
        logger.debug("Dialog: %s - %s", dialog.type, dialog.message)
        try:
            await self._pending_dialogs.put(dialog)
        except Exception:
            await dialog.dismiss()

    async def handle_dialog(self, accept: bool = True, text: str = None) -> bool:
        """Handle next pending dialog."""
        try:
            dialog = await asyncio.wait_for(
                self._pending_dialogs.get(), timeout=5.0
            )
            if accept:
                if text:
                    await dialog.accept(prompt_text=text)
                else:
                    await dialog.accept()
            else:
                await dialog.dismiss()
            return True
        except (asyncio.TimeoutError, Exception):
            return False

    async def dismiss_all_dialogs(self):
        """Dismiss all pending dialogs."""
        while not self._pending_dialogs.empty():
            try:
                dialog = self._pending_dialogs.get_nowait()
                await dialog.dismiss()
            except Exception:
                break

    async def _on_popup(self, popup):
        """Handle new popup window."""
        logger.debug("Popup opened: %s", popup.url)
        # Auto-close popups unless configured otherwise
        try:
            await popup.close()
        except Exception:
            pass

    async def _on_console(self, msg):
        """Handle console messages."""
        if self.debug and msg.type == 'error':
            logger.debug("Console error: %s", msg.text)

    # ─── MISC ──────────────────────────────────────────────────────

    async def inject_css(self, css: str):
        """Inject custom CSS into the page."""
        try:
            await self.page.add_style_tag(content=css)
        except Exception:
            pass

    async def inject_js(self, js: str):
        """Inject custom JavaScript into the page."""
        try:
            await self.page.add_script_tag(content=js)
        except Exception:
            pass

    async def emulate_network(self, network_type: str = 'online'):
        """Emulate network conditions (online/offline/throttled)."""
        try:
            if network_type == 'offline':
                await self.context.set_offline(True)
            else:
                await self.context.set_offline(False)
        except Exception:
            pass

    async def get_performance_metrics(self) -> Dict:
        """Get performance metrics for the current page."""
        try:
            metrics = await self.page.evaluate("""() => ({
                domContentLoaded: performance.getEntriesByType('navigation')[0]?.domContentLoadEventEnd || 0,
                loadTime: performance.getEntriesByType('navigation')[0]?.loadEventEnd || 0,
                domNodes: document.querySelectorAll('*').length,
                scripts: document.querySelectorAll('script').length,
                images: document.querySelectorAll('img').length,
                links: document.querySelectorAll('a').length,
            })""")
            self.state.performance_metrics = metrics
            return metrics
        except Exception:
            return {}

    async def emulate_device(self, device_name: str):
        """Emulate a device (iPhone, iPad, Pixel, etc)."""
        try:
            from playwright.async_api import devices
            if device_name in devices:
                device = devices[device_name]
                await self.context.emulate(device)
        except Exception:
            pass

    async def focus_element(self, selector: str) -> bool:
        """Focus on an element."""
        try:
            await self.page.locator(selector).focus()
            return True
        except Exception:
            return False

    async def blur_element(self, selector: str) -> bool:
        """Remove focus from an element."""
        try:
            await self.page.locator(selector).blur()
            return True
        except Exception:
            return False

    async def evaluate(self, js: str) -> Any:
        """Evaluate JavaScript and return result."""
        try:
            return await self.page.evaluate(js)
        except Exception:
            return None

    async def get_html_outer(self, selector: str) -> Optional[str]:
        """Get outer HTML of an element."""
        try:
            return await self.page.locator(selector).evaluate('el => el.outerHTML')
        except Exception:
            return None

    # ─── INTERNAL HELPERS ──────────────────────────────────────────

    async def _get_current_mouse_position(self) -> Dict[str, int]:
        """Get current mouse position from page."""
        try:
            return await self.page.evaluate("""() => ({
                x: window.mouseX || 0,
                y: window.mouseY || 0,
            })""")
        except Exception:
            return {'x': 0, 'y': 0}

    async def _human_move_to(
        self, from_x: int, from_y: int, to_x: int, to_y: int
    ):
        """Move mouse with human-like trajectory."""
        async def on_move(x: int, y: int):
            try:
                await self.page.mouse.move(x, y)
            except Exception:
                pass

        await self.human_mouse.move_to(
            (from_x, from_y),
            (to_x, to_y),
            on_move=on_move,
        )
        try:
            await self.page.mouse.move(int(to_x), int(to_y))
        except Exception:
            pass

    async def _on_page_load(self, page=None):
        """Handle page load event."""
        try:
            p = page or self.page
            self.state.url = p.url
            self.state.title = await p.title() or ""
            if self.debug:
                logger.info("Page loaded: %s", self.state.title[:80])
        except Exception:
            pass

    async def _on_page_crash(self, page=None):
        """Handle page crash."""
        logger.error("Page crashed!")
        self.state.is_connected = False
        self.state.errors_since_last_health += 1

    # ─── LIFECYCLE ─────────────────────────────────────────────────

    async def close(self):
        """Close the browser and cleanup."""
        try:
            await self.dismiss_all_dialogs()
        except Exception:
            pass

        if self.page:
            try:
                await self.page.close()
            except Exception:
                pass
            self.page = None

        if self.context:
            try:
                await self.context.close()
            except Exception:
                pass
            self.context = None

        if self.browser:
            try:
                await self.browser.close()
            except Exception:
                pass
            self.browser = None

        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception:
                pass
            self.playwright = None

        self.state.is_connected = False
        self.state.last_action_time = time.time()
        logger.info("Browser closed")

    async def restart(self) -> bool:
        """Restart the browser entirely."""
        await self.close()
        return await self.start()

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# Factory functions
def create_browser_agent(
    headless: bool = False,
    slow: bool = True,
    debug: bool = False,
    undetected: bool = False,
) -> BrowserAgent:
    """Create a configured BrowserAgent instance."""
    if undetected:
        config = BrowserConfig.undetected()
    else:
        config = BrowserConfig(
            headless=headless,
            stealth=True,
            window_width=1280,
            window_height=800,
            slow_mo=50 if slow else 0,
        )

    mouse = get_cautious_human_mouse() if slow else get_human_mouse()
    agent = BrowserAgent(config=config, human_mouse=mouse, debug=debug)
    return agent
