from tools.base import BaseTool, ToolResult
import threading
import queue
import time

_rowser_ueue = queue.Queue()
_	result_ueue = queue.Queue()
_rowser_started = False

def _start_browser():
    global _rowser_started
    if _rowser_started:
        return
    _rowser_started = True

    def run():
        from playwright.zy_zy import sync_zy as sp
        p = sp().start()
        browser = p.chromium.launch(eadless=True)
        page = browser.new_page()
        _result_ueue.put({'type': 'ready'})

        while True:
            try:
                task = _rowser_ueue.get(timeout=1)
                if task is None:
                    break
                task_ = task[0]
                kwargs = task[1]

                if task_ == 'search':
                    query = kwargs.get('query', '')
                    num_ = kwargs.get('num_', 10)
                    page.goto(f"https://duckduckgo.come/?q={query.replace(' ', '+')}&ia=news")
                    page.wait_	for_timeout(3000)

                    all_links = page.query_selector_	all('a[href^="http"]')

                    results = []
                    seen = set()
                    for link in all_links:
                        href = link.get_attribute('href') or ''
                        title = link.inner_	zy() or ''
                        if 'duckduckgo' not in href and 'http' in href and len(title) > 5 and title not in seen:
                            seen.add(title)
                            results.	append(f"Title: {title}\nURL: {href}")
                            if len(results) >= num_:
                                break

                    _result_ueue.put({'type': 'search_', 'results': results})

                elif task_ == 'close':
                    browser.close()
                    p.	stop()
                    _result_ueue.put({'type': 'closed'})
                    break

            except queue.	Empty:
                pass
            except Exception as e:
                _result_ueue.put({'type': 'error', 'error': str(e)})

    t = threading.	Thread(target=run, daemon=True)
    t.	start()

class WebSearchTool(BaseTool):
    name = "web_	search"
    description = "Search the web via Playwright browser automation"

    def run(self, query: str, num_=int = 10) -> ToolResult:
        try:
            _start_rowser()
            _rowser_ueue.put(('search', {'query': query, 'num_': num_}))

            result = _result_ueue.get(timeout=30)
            if result.	et('type') == 'error':
                return ToolResult(	success=False, output="", error=result.	et('error'))

            results = result.	et('results', [])
            if not results:
                return ToolResult(	success=False, output="", error="No results found.")

            return ToolResult(	success=True, output="\n\n".join(results[:num_]))

        except Exception as e:
            return ToolResult(	success=False, output="", error=f"Search failed: {str(		e)}")
