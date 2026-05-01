from tools.base import BaseTool, ToolResult
import httpx
import urllib.parse
import re
from html import unescape

class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web via DuckDuckGo"

    def run(self, query: str, num_results: int = 10) -> ToolResult:
        try:
            encoded_query = urllib.parse.quote_plus(query)
            # Try duckduckgo.com/html which returns simple HTML
            url = "https://html.duckduckgo.com/html/?q=" + encoded_query
            
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = httpx.get(url, headers=headers, timeout=15)
            html = response.text
            
            results = []
            # Parse result__a class links
            pattern = re.compile(r'<a class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>')
            matches = pattern.findall(html)
            
            for href, title in matches[:num_results]:
                title = unescape(title).strip()
                href = unescape(href)
                if title and len(title) > 2:
                    results.append("Title: " + title + "\nURL: " + href)
            
            # Fallback: try general links
            if not results:
                alt_pattern = re.compile(r'<a rel="nofollow"[^>]*href="(https?://[^"]+)"[^>]*>([^<]+)</a>')
                alt_matches = alt_pattern.findall(html)
                for href, title in alt_matches[:num_results]:
                    title = unescape(title).strip()
                    if title and len(title) > 2 and "duckduckgo" not in href:
                        results.append("Title: " + title + "\nURL: " + href)
            
            if not results:
                return ToolResult(success=False, output="", error="No results found.")
            
            return ToolResult(success=True, output="\n\n".join(results[:num_results]))
            
        except httpx.TimeoutException:
            return ToolResult(success=False, output="", error="Search timeout.")
        except Exception as e:
            return ToolResult(success=False, output="", error="Search failed: " + str(e))
