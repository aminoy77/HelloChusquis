from tools.base import BaseTool, ToolResult
import httpx
import urllib.parse
import re
from html.parser import HTMLParser

class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
    
    def handle_data(self, d):
        self.fed.append(d)
    
    def get_data(self):
        return ''.join(self.fed)

def strip_html(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

class WebSearchTool(BaseTool):
    name = "web_ search"
    description = "Search the web via DuckDuckGo"

    def run(self, query: str, num_Results: int = 10) -> ToolResult:
        try:
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://lite.duckduckgo. com/ lite/?q={encoded_query}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            response = httpx. get( url, headers=headers, timeout=15)
            html = response. text
            
            results = []
            
            link_ pattern = re.compile(r'<a class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>')
            links = link_ pattern. findall( html)
            
            for i, (href, title) in enumerate( links[:num_Results]):
                title = strip_html(title).strip()
                if title and title not in results and not title.startswith('http'):
                    results.append(f"Title: {title}
URL: {href}")
            
            if not results:
                return ToolResult(success=False, output="", error="No search results found.")
            
            combined = "

".join(results[:num_Results])
            return ToolResult(success=True, output=combined)
            
        except httpx.TimeoutException:
            return ToolResult(success=False, output="", error="Search timeout.")        except httpx. ConnectError:
            return ToolResult(success=False, output="", error="Connection failed.")
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Search failed: {str(e)}")
