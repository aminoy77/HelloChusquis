from tools.base import BaseTool, ToolResult
import httpx


class PipedriveTool(BaseTool):
    name = "pipedrive"
    description = "Pipedrive CRM - deals"

    def run(self, action: str = "list", **kwargs) -> ToolResult:
        token = self.config.get("token")
        if not token:
            return ToolResult(False, "", "Pipedrive token required")

        base_url = "https://api.pipedrive.com/v1"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            if action == "list_deals":
                r = httpx.get(f"{base_url}/deals", headers=headers, timeout=30)
                return ToolResult(True, str(r.json()))

            if action == "list_persons":
                r = httpx.get(f"{base_url}/persons", headers=headers, timeout=30)
                return ToolResult(True, str(r.json()))

            return ToolResult(False, "", f"Unknown: {action}")
        except Exception as e:
            return ToolResult(False, "", str(e))


def run(action: str = "list", **kwargs):
    return PipedriveTool().run(action, **kwargs)