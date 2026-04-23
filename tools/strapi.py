from tools.base import BaseTool, ToolResult
import httpx


class StrapiTool(BaseTool):
    name = "strapi"
    description = "Strapi - headless CMS"

    def run(self, action: str = "list", **kwargs) -> ToolResult:
        url = self.config.get("url")
        token = self.config.get("token")
        if not url:
            return ToolResult(False, "", "Strapi URL required")

        headers = {"Authorization": f"Bearer {token}"}

        try:
            if action == "list":
                collection = kwargs.get("collection", "articles")
                r = httpx.get(f"{url}/api/{collection}", headers=headers, timeout=30)
                return ToolResult(True, str(r.json()))
            return ToolResult(False, "", f"Unknown: {action}")
        except Exception as e:
            return ToolResult(False, "", str(e))


def run(action: str = "list", **kwargs):
    return StrapiTool().run(action, **kwargs)