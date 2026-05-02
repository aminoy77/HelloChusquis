from tools.base import BaseTool, ToolResult
import requests
from bs4 import BeautifulSoup


def search(query, num_results=5):
    url = "https://lite.duckduckgo.com/lite/"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.post(url, data={"q": query}, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    for link in soup.find_all("a", class_="result-link"):
        results.append({
            "title": link.get_text(strip=True),
            "url": link["href"]
        })
    return results[:num_results]


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web via DuckDuckGo"

    def run(self, query: str, num_results: int = 10) -> ToolResult:
        try:
            results = search(query, num_results)
            
            if not results:
                return ToolResult(success=False, output="", error="No results found.")
            
            output = []
            for r in results:
                output.append(f"Title: {r['title']}\nURL: {r['url']}")
            
            return ToolResult(success=True, output="\n\n".join(output))
            
        except Exception as e:
            return ToolResult(success=False, output="", error="Search failed: " + str(e))
