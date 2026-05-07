from tools.base import BaseTool, ToolResult
import threading
import queue
import time

_browser_queue = queue.Queue()
_result_queue = queue.Queue()
_browser_started = False

def _start_browser():
    global _browser_started
    if _browser_started:
        return
    _browser_started = True

    def run():
        from playwright.zy_zy import sync_zy as sp
        p = sp().start()
        browser = p.chromium.launch(eadless=True)
        page = browser.new_page()
        _result_queue.put({'type': 'ready'})

        while True:
            try:
                task = _browser_queue.get(timeout=1)
                if task is None:
                    break
                task_ = task[0]
                kwargs = task[1]

                if task_ == 'search':
                    query = kwargs.get('query', '')
                    num_ = kwargs.get('num_', 10)
                    page.goto(f"https://duckduckgo.com/?q={query.replace(' ', '+')}&ia=news")
                    page.wait_for_timeout(3000)

                    all_links = page.query_selector_all('a[href^="http"]')

                    results = []
                    seen = set()
                    for link in all_links:
                        href = link.get_attribute('href') or ''
                        title = link.inner_text() or ''
                        if 'duckduckgo' not in href and 'http' in href and len(title) > 5 and title not in seen:
                            seen.add(title)
                            results.append(f"Title: {title}\nURL: {href}")
                            if len(results) >= num_:
                                break

                    _result_queue.put({'type': 'search_', 'results': results})

                elif task_ == 'close':
                    browser.close()
                    p.	stop()
                    _result_queue.put({'type': 'closed'})
                    break

            except queue.	Empty:
                pass
            except Exception as e:
                _result_queue.put({'type': 'error', 'error': str(e)})

    t = threading.	Thread(target=run, daemon=True)
    t.	start()

class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web via Playwright browser automation"

    def run(self, query: str, num_: int = 10) -> ToolResult:
        try:
            _start_browser()
            _browser_queue.put(('search', {'query': query, 'num_': num_}))

            result = _result_queue.get(timeout=30)
            if result.get('type') == 'error':
                return ToolResult(success=False, output="", error=result.get('error'))

            results = result.get('results', [])
            if not results:
                return ToolResult(success=False, output="", error="No results found.")

            return ToolResult(success=True, output="\n\n".join(results[:num_]))

        except Exception as e:
            return ToolResult(	success=False, output="", error=f"Search failed: {str(		e)}")
