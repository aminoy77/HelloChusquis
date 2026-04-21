from tools.base import BaseTool, ToolResult
import httpx
import urllib.parse


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Busca resultados en la web mediante DuckDuckGo"

    def run(self, query: str) -> ToolResult:
        try:
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_redirect=1&skip_disambig=1"

            headers = {
                "User-Agent": "Mozilla/5.0"
            }

            response = httpx.get(url, headers=headers, timeout=10)
            data = response.json()

            results = []

            # Abstract principal
            if 'AbstractText' in data and data['AbstractText']:
                results.append(data['AbstractText'])

            # Related Topics/Temas relacionados
            if 'RelatedTopics' in data:
                topics = [item.get("Text", "") for item in data["RelatedTopics"][:5]]
                results.extend(topics)

            if not results:
                return ToolResult(success=False, output="", error="No relevant results found.")

            combined_results = "\n---\n".join(results)
            truncated = combined_results[:2000]
            return ToolResult(success=True, output=truncated)
        
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Web search failed: {str(e)}")
