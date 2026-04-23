from tools.base import BaseTool, ToolResult
import httpx


class JotformTool(BaseTool):
    name = "jotform"
    description = "Jotform - online forms"

    def run(self, action: str = "list", **kwargs) -> ToolResult:
        token = self.config.get("token")
        if not token:
            return ToolResult(False, "", "Jotform token required")

        base_url = "https://api.jotform.com"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        try:
            if action == "list_forms":
                r = httpx.get(f"{base_url}/user/forms", headers=headers, timeout=30)
                return ToolResult(True, str(r.json()))

            if action == "get_submissions":
                form_id = kwargs.get("form_id")
                r = httpx.get(f"{base_url}/form/{form_id}/submissions", headers=headers, timeout=30)
                return ToolResult(True, str(r.json()))

            return ToolResult(False, "", f"Unknown: {action}")
        except Exception as e:
            return ToolResult(False, "", str(e))


def run(action: str = "list", **kwargs):
    return JotformTool().run(action, **kwargs)