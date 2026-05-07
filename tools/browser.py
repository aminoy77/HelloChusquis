"""
Browser automation tools for HelloChusquis.
Persistent browser with human-like mouse movements.
"""

import asyncio
import threading
import queue
import uuid
from typing import Any

from core.browser_agent import BrowserAgent, create_browser_agent


class PersistentBrowser:
    """Manages a persistent browser instance that stays open."""

    _instance = None
    _agent: BrowserAgent = None
    _loop = None
    _thread = None
    _task_queue = None
    _result_queue = None
    _started = False

    @classmethod
    def get_instance(cls) -> 'PersistentBrowser':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def start(self):
        """Start the persistent browser thread."""
        if self._started and self._thread and self._thread.is_alive():
            return

        self._task_queue = queue.Queue()
        self._result_queue = queue.Queue()

        def run_browser():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            async def init():
                agent = create_browser_agent(headless=False, slow=True, debug=True)
                success = await agent.start()
                if success:
                    self._agent = agent
                    print('[PersistentBrowser] Started')
                else:
                    print('[PersistentBrowser] Failed to start')
                    self._result_queue.put({'success': False, 'error': 'Failed to start browser'})
                    return

                while True:
                    try:
                        data = self._task_queue.get(timeout=0.5)
                        if data is None:
                            break

                        task_name, kwargs = data

                        if task_name == 'navigate':
                            url = kwargs.get('url', '')
                            if not url.startswith(('http://', 'https://')):
                                url = 'https://' + url
                            success = await self._agent.navigate(url)
                            self._result_queue.put({
                                'success': success,
                                'url': self._agent.state.url,
                                'title': self._agent.state.title
                            })

                        elif task_name == 'click':
                            success = await self._agent.click_element(
                                selector=kwargs.get('selector'),
                                text=kwargs.get('text'),
                                xpath=kwargs.get('xpath')
                            )
                            self._result_queue.put({'success': success})

                        elif task_name == 'type':
                            success = await self._agent.type_text(
                                kwargs.get('text', ''),
                                selector=kwargs.get('selector')
                            )
                            self._result_queue.put({'success': success})

                        elif task_name == 'scroll':
                            await self._agent.scroll(
                                direction=kwargs.get('direction', 'down'),
                                amount=kwargs.get('amount', 3)
                            )
                            self._result_queue.put({'success': True})

                        elif task_name == 'screenshot':
                            path = kwargs.get('path') or f"screenshot_{uuid.uuid4().hex[:8]}.png"
                            saved_path = await self._agent.save_screenshot(path)
                            self._result_queue.put({'success': bool(saved_path), 'path': saved_path})

                        elif task_name == 'get_text':
                            text = await self._agent.get_text_content(kwargs.get('selector'))
                            self._result_queue.put({'success': True, 'text': text[:5000]})

                        elif task_name == 'search':
                            success = await self._agent.search(
                                kwargs.get('engine', 'google'),
                                kwargs.get('query', '')
                            )
                            self._result_queue.put({'success': success, 'url': self._agent.state.url})

                        elif task_name == 'find':
                            elements = await self._agent.find_elements(kwargs.get('pattern', ''))
                            self._result_queue.put({
                                'success': True,
                                'count': len(elements),
                                'elements': elements[:20]
                            })

                        elif task_name == 'close':
                            await self._agent.close()
                            self._result_queue.put({'success': True})
                            break

                        else:
                            self._result_queue.put({'success': False, 'error': f'Unknown task: {task_name}'})

                    except queue.Empty:
                        pass
                    except Exception as e:
                        self._result_queue.put({'success': False, 'error': str(e)})

                self._agent = None
                print('[PersistentBrowser] Closed')

            self._loop.run_until_complete(init())

        self._thread = threading.Thread(target=run_browser, daemon=True)
        self._thread.start()
        self._started = True

        # Wait for browser to initialize
        import time
        time.sleep(3)

    def stop(self):
        """Stop the browser."""
        if self._task_queue:
            self._task_queue.put(None)

    def do(self, task_name: str, **kwargs) -> dict:
        """Execute a browser task."""
        if not self._started or not self._thread or not self._thread.is_alive():
            self.start()

        self._task_queue.put((task_name, kwargs))

        try:
            result = self._result_queue.get(timeout=60)
            return result
        except Exception:
            return {'success': False, 'error': 'Timeout'}


def browser_open(url: str) -> dict:
    """Open a URL in the browser."""
    pb = PersistentBrowser.get_instance()
    return pb.do('navigate', url=url)


def browser_click(selector: str = None, text: str = None, xpath: str = None) -> dict:
    """Click an element on the page."""
    pb = PersistentBrowser.get_instance()
    return pb.do('click', selector=selector, text=text, xpath=xpath)


def browser_type(text: str, selector: str = None) -> dict:
    """Type text into a field."""
    pb = PersistentBrowser.get_instance()
    return pb.do('type', text=text, selector=selector)


def browser_scroll(direction: str = 'down', amount: int = 3) -> dict:
    """Scroll the page."""
    pb = PersistentBrowser.get_instance()
    return pb.do('scroll', direction=direction, amount=amount)


def browser_screenshot(path: str = None) -> dict:
    """Take a screenshot."""
    pb = PersistentBrowser.get_instance()
    return pb.do('screenshot', path=path)


def browser_get_text(selector: str = None) -> dict:
    """Get text content from the page."""
    pb = PersistentBrowser.get_instance()
    return pb.do('get_text', selector=selector)


def browser_search(query: str, engine: str = 'google') -> dict:
    """Search the web."""
    pb = PersistentBrowser.get_instance()
    return pb.do('search', query=query, engine=engine)


def browser_find(pattern: str) -> dict:
    """Find elements matching a pattern."""
    pb = PersistentBrowser.get_instance()
    return pb.do('find', pattern=pattern)


def browser_close() -> dict:
    """Close the browser."""
    pb = PersistentBrowser.get_instance()
    result = pb.do('close')
    pb.stop()
    return result