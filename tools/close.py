from tools.base import BaseTool, ToolResult
import httpx


class CloseTool(BaseTool):
    name = "close"
    description = "Close CRM - sales pipeline"

    def run(self, action: str = "list", **kwargs) -> ToolResult:
        token = self.config.get("token")
        if not token:
            return ToolResult(False, "", "Close token required")

        base_url = "https://api.close.com/api/v1"
        headers = {"Authorization": f"Token {token}"}

        try:
            if action == "list_leads":
                r = httpx.get(f"{base_url}/leads", headers=headers, timeout=30)
                return ToolResult(True, str(r.json()))

            if action == "create_lead":
                r = httpx.post(f"{base_url}/leads", headers=headers, json=kwargs, timeout=30)
                return ToolResult(True, str(r.json()))

            return ToolResult(False, "", f"Unknown: {action}")
        except Exception as e:
            return ToolResult(False, "", str(e))


def run(action: str = "list", **kwargs):
    return CloseTool().run(action, **kwargs)