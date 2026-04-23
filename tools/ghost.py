from tools.base import BaseTool, ToolResult
import httpx


class GhostTool(BaseTool):
    name = "ghost"
    description = "Ghost CMS publishing"

    def run(self, action: str = "list", **kwargs) -> ToolResult:
        token = self.config.get("token")
        if not token:
            return ToolResult(False, "", "Token required")
        headers = {"Authorization": token}
        try:
            if action == "list_posts":
                r = httpx.get("https://your-site.ghost.io/api/admin/posts", headers=headers, timeout=30)
                return ToolResult(True, str(r.json()))
            return ToolResult(False, "", f"Unknown: {action}")
        except Exception as e:
            return ToolResult(False, "", str(e))

def run(action: str = "list", **kwargs):
    return GhostTool().run(action, **kwargs)