"""
Browser automation tools for HelloChusquis.
Persistent browser with human-like mouse movements, auto-recovery, health checks.
"""

import asyncio
import logging
import os
import threading
import queue
import time
import uuid
from typing import Any, Optional

from core.browser_agent import BrowserAgent, create_browser_agent

logger = logging.getLogger("persistent_browser")


class BrowserError(Exception):
    """Base exception for browser operations."""
    pass


class ConnectionError(BrowserError):
    """Browser not connected or unreachable."""
    pass


class TimeoutError(BrowserError):
    """Browser operation timed out."""
    pass


class PersistentBrowser:
    """
    Manages a persistent browser instance with:
    - Automatic reconnection on crash
    - Health checks before each operation
    - Proper async event loop in daemon thread
    - Task timeouts and error reporting
    - Warm-up: browser stays ready between calls
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._agent: Optional[BrowserAgent] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._task_queue: queue.Queue = queue.Queue()
        self._result_queues: dict = {}
        self._result_lock = threading.Lock()
        self._next_task_id = 0
        self._started = False
        self._stopped = False
        self._init_event = threading.Event()

    @classmethod
    def get_instance(cls) -> 'PersistentBrowser':
        """Get or create the singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _get_task_id(self) -> str:
        """Generate a unique task ID."""
        with self._result_lock:
            tid = f"task_{self._next_task_id}"
            self._next_task_id += 1
            return tid

    def start(self, headless: bool = False, undetected: bool = True):
        """Start the persistent browser in a background thread."""
        with self._result_lock:
            if self._started and self._thread and self._thread.is_alive():
                return
            if self._thread and self._thread.is_alive() and not self._started:
                # Already starting - wait for it
                if self._init_event.wait(timeout=30):
                    return
                else:
                    # Previous init timed out, restart fresh
                    pass

            self._stopped = False
            self._init_event.clear()

        def run_browser_loop():
            """Run the browser event loop in a daemon thread."""
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self._browser_lifecycle())
            self._loop.close()

        self._thread = threading.Thread(
            target=run_browser_loop,
            daemon=True,
            name="persistent-browser",
        )
        self._thread.start()

        # Wait for browser to initialize (with timeout)
        if not self._init_event.wait(timeout=30):
            logger.error("Browser initialization timed out")
            self._started = False
            raise BrowserError("Browser initialization timed out after 30s")

        self._started = True
        logger.info("PersistentBrowser ready")

    async def _browser_lifecycle(self):
        """Main browser lifecycle with auto-recovery."""
        while not self._stopped:
            try:
                # Create and start the browser agent
                self._agent = create_browser_agent(
                    headless=False,
                    slow=True,
                    debug=True,
                    undetected=True,
                )
                success = await self._agent.start()
                if not success:
                    logger.error("Failed to start browser agent")
                    await asyncio.sleep(3)
                    continue

                self._init_event.set()
                logger.info("Browser agent started successfully")

                # Main task processing loop
                await self._task_processing_loop()

            except Exception as e:
                logger.error("Browser lifecycle error: %s", e)
                self._agent = None
                await asyncio.sleep(2)

    async def _task_processing_loop(self):
        """Process tasks from the queue."""
        while not self._stopped and self._agent and self._agent.state.is_connected:
            try:
                # Periodically check health
                try:
                    healthy = await asyncio.wait_for(
                        self._agent.health_check(), timeout=5.0
                    )
                    if not healthy:
                        logger.warning("Browser health check failed, restarting...")
                        break
                except asyncio.TimeoutError:
                    logger.warning("Health check timed out")
                    break

                # Process next task with short timeout
                try:
                    task_id, task_name, kwargs = await asyncio.wait_for(
                        self._get_task_async(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # Execute the task
                try:
                    result = await self._execute_task(task_name, kwargs)
                except Exception as e:
                    result = {'success': False, 'error': str(e)}

                # Send result back
                with self._result_lock:
                    if task_id in self._result_queues:
                        self._result_queues[task_id].put(result)
                        del self._result_queues[task_id]

            except Exception as e:
                logger.error("Task processing error: %s", e)
                await asyncio.sleep(0.5)

    async def _get_task_async(self):
        """Get next task from queue asynchronously."""
        while True:
            try:
                return self._task_queue.get_nowait()
            except queue.Empty:
                await asyncio.sleep(0.1)

    async def _execute_task(self, task_name: str, kwargs: dict) -> dict:
        """Execute a browser task."""
        if not self._agent:
            return {'success': False, 'error': 'Browser not initialized'}

        handlers = {
            'navigate': self._handle_navigate,
            'click': self._handle_click,
            'double_click': self._handle_double_click,
            'right_click': self._handle_right_click,
            'type': self._handle_type,
            'scroll': self._handle_scroll,
            'scroll_to_element': self._handle_scroll_to_element,
            'scroll_to_bottom': self._handle_scroll_to_bottom,
            'scroll_to_top': self._handle_scroll_to_top,
            'screenshot': self._handle_screenshot,
            'element_screenshot': self._handle_element_screenshot,
            'get_text': self._handle_get_text,
            'get_visible_text': self._handle_get_visible_text,
            'get_html': self._handle_get_html,
            'get_url': self._handle_get_url,
            'get_title': self._handle_get_title,
            'search': self._handle_search,
            'find': self._handle_find,
            'wait_for_element': self._handle_wait_for_element,
            'wait_for_navigation': self._handle_wait_for_navigation,
            'hover': self._handle_hover,
            'fill_form': self._handle_fill_form,
            'select_option': self._handle_select_option,
            'submit_form': self._handle_submit_form,
            'upload_file': self._handle_upload_file,
            'check_checkbox': self._handle_check_checkbox,
            'execute_script': self._handle_execute_script,
            'get_cookies': self._handle_get_cookies,
            'clear_cookies': self._handle_clear_cookies,
            'get_pages': self._handle_get_pages,
            'switch_to_page': self._handle_switch_to_page,
            'open_new_tab': self._handle_open_new_tab,
            'close_current_tab': self._handle_close_current_tab,
            'press_key': self._handle_press_key,
            'go_back': self._handle_go_back,
            'go_forward': self._handle_go_forward,
            'reload': self._handle_reload,
            'inject_css': self._handle_inject_css,
            'inject_js': self._handle_inject_js,
            'close': self._handle_close,
            'handle_dialog': self._handle_dialog,
            'get_performance_metrics': self._handle_get_performance_metrics,
            'emulate_network': self._handle_emulate_network,
            'health': self._handle_health,
        }

        handler = handlers.get(task_name)
        if not handler:
            return {'success': False, 'error': f'Unknown task: {task_name}'}

        return await handler(**kwargs)

    # ─── TASK HANDLERS ────────────────────────────────────────────

    async def _handle_navigate(self, url: str = '', **kwargs) -> dict:
        if not url:
            return {'success': False, 'error': 'URL required'}
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        success = await self._agent.navigate(url)
        return {
            'success': success,
            'url': self._agent.state.url,
            'title': self._agent.state.title,
        }

    async def _handle_click(self, **kwargs) -> dict:
        success = await self._agent.click_element(
            selector=kwargs.get('selector'),
            text=kwargs.get('text'),
            xpath=kwargs.get('xpath'),
            index=kwargs.get('index', 0),
        )
        return {'success': success}

    async def _handle_double_click(self, **kwargs) -> dict:
        success = await self._agent.double_click(
            selector=kwargs.get('selector'),
            text=kwargs.get('text'),
            xpath=kwargs.get('xpath'),
        )
        return {'success': success}

    async def _handle_right_click(self, **kwargs) -> dict:
        success = await self._agent.right_click(
            selector=kwargs.get('selector'),
            text=kwargs.get('text'),
            xpath=kwargs.get('xpath'),
        )
        return {'success': success}

    async def _handle_type(self, text: str = '', **kwargs) -> dict:
        success = await self._agent.type_text(
            text=text,
            selector=kwargs.get('selector'),
            clear_first=kwargs.get('clear_first', True),
        )
        return {'success': success}

    async def _handle_scroll(self, **kwargs) -> dict:
        success = await self._agent.scroll(
            direction=kwargs.get('direction', 'down'),
            amount=kwargs.get('amount', 3),
        )
        return {'success': success}

    async def _handle_scroll_to_element(self, **kwargs) -> dict:
        success = await self._agent.scroll_to_element(kwargs.get('selector', ''))
        return {'success': success}

    async def _handle_scroll_to_bottom(self, **kwargs) -> dict:
        success = await self._agent.scroll_to_bottom()
        return {'success': success}

    async def _handle_scroll_to_top(self, **kwargs) -> dict:
        success = await self._agent.scroll_to_top()
        return {'success': success}

    async def _handle_screenshot(self, **kwargs) -> dict:
        path = kwargs.get('path') or f"screenshot_{uuid.uuid4().hex[:8]}.png"
        full_page = kwargs.get('full_page', False)
        saved_path = await self._agent.save_screenshot(path, full_page=full_page)
        # Also return the bytes for direct consumption
        screenshot_bytes = await self._agent.take_screenshot(full_page=full_page)
        return {
            'success': bool(saved_path),
            'path': saved_path,
            'data': screenshot_bytes.hex() if screenshot_bytes else '',
        }

    async def _handle_element_screenshot(self, **kwargs) -> dict:
        path = kwargs.get('path') or f"element_{uuid.uuid4().hex[:8]}.png"
        saved_path = await self._agent.element_screenshot(
            kwargs.get('selector', ''), path
        )
        return {'success': bool(saved_path), 'path': saved_path}

    async def _handle_get_text(self, **kwargs) -> dict:
        text = await self._agent.get_text_content(kwargs.get('selector'))
        return {'success': True, 'text': text[:10000]}

    async def _handle_get_visible_text(self, **kwargs) -> dict:
        text = await self._agent.get_visible_text()
        return {'success': True, 'text': text[:10000]}

    async def _handle_get_html(self, **kwargs) -> dict:
        html = await self._agent.get_html(kwargs.get('selector'))
        return {'success': True, 'html': html[:50000]}

    async def _handle_get_url(self, **kwargs) -> dict:
        url = await self._agent.get_url()
        return {'success': True, 'url': url}

    async def _handle_get_title(self, **kwargs) -> dict:
        title = await self._agent.get_title()
        return {'success': True, 'title': title}

    async def _handle_search(self, **kwargs) -> dict:
        success = await self._agent.search(
            kwargs.get('query', ''),
            kwargs.get('engine', 'google'),
        )
        return {'success': success, 'url': self._agent.state.url}

    async def _handle_find(self, **kwargs) -> dict:
        elements = await self._agent.find_elements(kwargs.get('pattern', ''))
        return {
            'success': True,
            'count': len(elements),
            'elements': elements[:30],
        }

    async def _handle_wait_for_element(self, **kwargs) -> dict:
        success = await self._agent.wait_for_element(
            kwargs.get('selector', ''),
            timeout=kwargs.get('timeout', 30),
        )
        return {'success': success}

    async def _handle_wait_for_navigation(self, **kwargs) -> dict:
        success = await self._agent.wait_for_navigation(
            timeout=kwargs.get('timeout', 30)
        )
        return {'success': success}

    async def _handle_hover(self, **kwargs) -> dict:
        success = await self._agent.hover_element(
            selector=kwargs.get('selector'),
            text=kwargs.get('text'),
            xpath=kwargs.get('xpath'),
        )
        return {'success': success}

    async def _handle_fill_form(self, **kwargs) -> dict:
        form_data = kwargs.get('form_data', {})
        filled = await self._agent.fill_form(form_data)
        return {'success': filled > 0, 'filled': filled}

    async def _handle_select_option(self, **kwargs) -> dict:
        success = await self._agent.select_option(
            kwargs.get('selector', ''),
            value=kwargs.get('value'),
            label=kwargs.get('label'),
            index=kwargs.get('index'),
        )
        return {'success': success}

    async def _handle_submit_form(self, **kwargs) -> dict:
        success = await self._agent.submit_form(kwargs.get('selector', 'form'))
        return {'success': success}

    async def _handle_upload_file(self, **kwargs) -> dict:
        success = await self._agent.upload_file(
            kwargs.get('selector', ''),
            kwargs.get('file_path', ''),
        )
        return {'success': success}

    async def _handle_check_checkbox(self, **kwargs) -> dict:
        success = await self._agent.check_checkbox(
            kwargs.get('selector', ''),
            checked=kwargs.get('checked', True),
        )
        return {'success': success}

    async def _handle_execute_script(self, **kwargs) -> dict:
        result = await self._agent.execute_script(kwargs.get('script', ''))
        return {'success': result is not None, 'result': str(result)[:5000]}

    async def _handle_get_cookies(self, **kwargs) -> dict:
        cookies = await self._agent.get_cookies()
        return {'success': True, 'cookies': cookies}

    async def _handle_clear_cookies(self, **kwargs) -> dict:
        await self._agent.clear_cookies()
        return {'success': True}

    async def _handle_get_pages(self, **kwargs) -> dict:
        count = await self._agent.get_page_count()
        return {'success': True, 'count': count}

    async def _handle_switch_to_page(self, **kwargs) -> dict:
        success = await self._agent.switch_to_page(kwargs.get('index', 0))
        return {'success': success}

    async def _handle_open_new_tab(self, **kwargs) -> dict:
        success = await self._agent.open_new_tab(kwargs.get('url'))
        return {'success': success}

    async def _handle_close_current_tab(self, **kwargs) -> dict:
        success = await self._agent.close_current_tab()
        return {'success': success}

    async def _handle_press_key(self, **kwargs) -> dict:
        success = await self._agent.press_key(kwargs.get('key', ''))
        return {'success': success}

    async def _handle_go_back(self, **kwargs) -> dict:
        success = await self._agent.go_back()
        return {'success': success}

    async def _handle_go_forward(self, **kwargs) -> dict:
        success = await self._agent.go_forward()
        return {'success': success}

    async def _handle_reload(self, **kwargs) -> dict:
        success = await self._agent.reload()
        return {'success': success}

    async def _handle_inject_css(self, **kwargs) -> dict:
        await self._agent.inject_css(kwargs.get('css', ''))
        return {'success': True}

    async def _handle_inject_js(self, **kwargs) -> dict:
        await self._agent.inject_js(kwargs.get('js', ''))
        return {'success': True}

    async def _handle_dialog(self, **kwargs) -> dict:
        success = await self._agent.handle_dialog(
            accept=kwargs.get('accept', True),
            text=kwargs.get('text'),
        )
        return {'success': success}

    async def _handle_get_performance_metrics(self, **kwargs) -> dict:
        metrics = await self._agent.get_performance_metrics()
        return {'success': True, 'metrics': metrics}

    async def _handle_emulate_network(self, **kwargs) -> dict:
        await self._agent.emulate_network(kwargs.get('network_type', 'online'))
        return {'success': True}

    async def _handle_health(self, **kwargs) -> dict:
        healthy = await self._agent.health_check()
        return {
            'success': healthy,
            'url': self._agent.state.url,
            'title': self._agent.state.title,
            'pages': len(self._agent.context.pages) if self._agent.context else 0,
        }

    async def _handle_close(self, **kwargs) -> dict:
        await self._agent.close()
        self._agent = None
        return {'success': True}

    # ─── PUBLIC API ───────────────────────────────────────────────

    def do(self, task_name: str, timeout: int = 60, **kwargs) -> dict:
        """
        Execute a browser task synchronously.

        Args:
            task_name: Name of the task to execute
            timeout: Maximum time to wait for result in seconds
            **kwargs: Task-specific parameters

        Returns:
            dict with 'success' key and task-specific data
        """
        if not self._started or not self._thread or not self._thread.is_alive():
            try:
                self.start()
            except BrowserError:
                return {'success': False, 'error': 'Failed to start browser'}

        task_id = self._get_task_id()
        result_queue = queue.Queue()

        with self._result_lock:
            self._result_queues[task_id] = result_queue

        self._task_queue.put((task_id, task_name, kwargs))

        try:
            result = result_queue.get(timeout=timeout)
            return result
        except queue.Empty:
            with self._result_lock:
                if task_id in self._result_queues:
                    del self._result_queues[task_id]
            return {'success': False, 'error': f'Task timed out after {timeout}s'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def stop(self):
        """Stop the browser."""
        self._stopped = True
        if self._task_queue:
            self._task_queue.put(('__stop__', '', {}))
        if self._agent:
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self._agent.close(), self._loop
                )
                future.result(timeout=10)
            except Exception:
                pass
        self._started = False

    @property
    def is_healthy(self) -> bool:
        """Quick health check without creating tasks."""
        if not self._agent:
            return False
        return self._agent.state.is_connected


# ─── CONVENIENCE FUNCTIONS ─────────────────────────────────────────

pb = PersistentBrowser()


def _ensure_browser():
    """Ensure browser is running (lazy start)."""
    if not pb._started:
        pb.start()
    return pb


def browser_open(url: str) -> dict:
    """Open a URL in the browser."""
    return _ensure_browser().do('navigate', url=url)


def browser_click(
    selector: str = None,
    text: str = None,
    xpath: str = None,
    index: int = 0,
) -> dict:
    """Click an element on the page."""
    return _ensure_browser().do(
        'click', selector=selector, text=text, xpath=xpath, index=index
    )


def browser_double_click(
    selector: str = None, text: str = None, xpath: str = None
) -> dict:
    """Double-click an element."""
    return _ensure_browser().do(
        'double_click', selector=selector, text=text, xpath=xpath
    )


def browser_right_click(
    selector: str = None, text: str = None, xpath: str = None
) -> dict:
    """Right-click an element."""
    return _ensure_browser().do(
        'right_click', selector=selector, text=text, xpath=xpath
    )


def browser_type(text: str, selector: str = None, clear_first: bool = True) -> dict:
    """Type text into a field."""
    return _ensure_browser().do(
        'type', text=text, selector=selector, clear_first=clear_first
    )


def browser_scroll(direction: str = 'down', amount: int = 3) -> dict:
    """Scroll the page."""
    return _ensure_browser().do('scroll', direction=direction, amount=amount)


def browser_screenshot(path: str = None, full_page: bool = False) -> dict:
    """Take a screenshot."""
    return _ensure_browser().do('screenshot', path=path, full_page=full_page)


def browser_get_text(selector: str = None) -> dict:
    """Get text content from the page."""
    return _ensure_browser().do('get_text', selector=selector)


def browser_search(query: str, engine: str = 'google') -> dict:
    """Search the web."""
    return _ensure_browser().do('search', query=query, engine=engine)


def browser_find(pattern: str) -> dict:
    """Find elements matching a pattern."""
    return _ensure_browser().do('find', pattern=pattern)


def browser_wait_for_element(selector: str, timeout: int = 30) -> dict:
    """Wait for element to appear."""
    return _ensure_browser().do('wait_for_element', selector=selector, timeout=timeout)


def browser_execute_script(script: str) -> dict:
    """Execute JavaScript on the page."""
    return _ensure_browser().do('execute_script', script=script)


def browser_get_cookies() -> dict:
    """Get all cookies."""
    return _ensure_browser().do('get_cookies')


def browser_get_url() -> dict:
    """Get current URL."""
    return _ensure_browser().do('get_url')


def browser_get_title() -> dict:
    """Get current page title."""
    return _ensure_browser().do('get_title')


def browser_wait_for_navigation(timeout: int = 30) -> dict:
    """Wait for page navigation."""
    return _ensure_browser().do('wait_for_navigation', timeout=timeout)


def browser_go_back() -> dict:
    """Go back in history."""
    return _ensure_browser().do('go_back')


def browser_go_forward() -> dict:
    """Go forward in history."""
    return _ensure_browser().do('go_forward')


def browser_reload() -> dict:
    """Reload the current page."""
    return _ensure_browser().do('reload')


def browser_press_key(key: str) -> dict:
    """Press a keyboard key."""
    return _ensure_browser().do('press_key', key=key)


def browser_scroll_to_element(selector: str) -> dict:
    """Scroll to a specific element."""
    return _ensure_browser().do('scroll_to_element', selector=selector)


def browser_open_new_tab(url: str = None) -> dict:
    """Open a new tab."""
    return _ensure_browser().do('open_new_tab', url=url)


def browser_switch_to_page(index: int = 0) -> dict:
    """Switch to a specific tab."""
    return _ensure_browser().do('switch_to_page', index=index)


def browser_fill_form(form_data: dict) -> dict:
    """Fill a form with data."""
    return _ensure_browser().do('fill_form', form_data=form_data)


def browser_submit_form(selector: str = 'form') -> dict:
    """Submit a form."""
    return _ensure_browser().do('submit_form', selector=selector)


def browser_hover(
    selector: str = None, text: str = None, xpath: str = None
) -> dict:
    """Hover over an element."""
    return _ensure_browser().do('hover', selector=selector, text=text, xpath=xpath)


def browser_health() -> dict:
    """Check browser health."""
    return _ensure_browser().do('health')


def browser_get_visible_text() -> dict:
    """Get visible text from the page."""
    return _ensure_browser().do('get_visible_text')


def browser_close() -> dict:
    """Close the browser."""
    result = _ensure_browser().do('close')
    pb.stop()
    return result
