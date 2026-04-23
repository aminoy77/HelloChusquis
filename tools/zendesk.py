from tools.base import BaseTool, ToolResult
import httpx


class ZendeskTool(BaseTool):
    name = "zendesk"
    description = "Zendesk - support tickets"

    def run(self, action: str = "list", **kwargs) -> ToolResult:
        domain = self.config.get("domain")
        token = self.config.get("token")
        if not domain or not token:
            return ToolResult(False, "", "Zendesk domain and token required")

        base_url = f"https://{domain}.zendesk.com/api/v2"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        try:
            if action == "list_tickets":
                r = httpx.get(f"{base_url}/tickets", headers=headers, timeout=30)
                return ToolResult(True, str(r.json()))

            if action == "create_ticket":
                r = httpx.post(f"{base_url}/tickets", headers=headers, json=kwargs, timeout=30)
                return ToolResult(True, str(r.json()))

            return ToolResult(False, "", f"Unknown: {action}")
        except Exception as e:
            return ToolResult(False, "", str(e))


def run(action: str = "list", **kwargs):
    return ZendeskTool().run(action, **kwargs)