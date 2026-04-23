from tools.base import BaseTool, ToolResult
import httpx


class TypeformTool(BaseTool):
    name = "typeform"
    description = "Typeform - forms and surveys"

    def run(self, action: str = "list", **kwargs) -> ToolResult:
        token = self.config.get("token")
        if not token:
            return ToolResult(False, "", "Typeform token required")

        base_url = "https://api.typeform.com"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            if action == "list_forms":
                r = httpx.get(f"{base_url}/forms", headers=headers, timeout=30)
                return ToolResult(True, str(r.json()))

            if action == "get_responses":
                form_id = kwargs.get("form_id")
                r = httpx.get(f"{base_url}/forms/{form_id}/responses", headers=headers, timeout=30)
                return ToolResult(True, str(r.json()))

            return ToolResult(False, "", f"Unknown: {action}")
        except Exception as e:
            return ToolResult(False, "", str(e))


def run(action: str = "list", **kwargs):
    return TypeformTool().run(action, **kwargs)