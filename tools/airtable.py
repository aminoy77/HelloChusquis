from tools.base import BaseTool, ToolResult
import httpx


class AirtableTool(BaseTool):
    name = "airtable"
    description = "Airtable - collaborative bases"

    def run(self, action: str = "list", **kwargs) -> ToolResult:
        token = self.config.get("token")
        if not token:
            return ToolResult(False, "", "Airtable token required")

        base_id = self.config.get("base_id")
        base_url = f"https://api.airtable.com/v0/{base_id}"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            if action == "list":
                table = kwargs.get("table", "Table1")
                r = httpx.get(f"{base_url}/{table}", headers=headers, timeout=30)
                return ToolResult(True, str(r.json()))

            if action == "create":
                r = httpx.post(base_url, headers=headers, json=kwargs, timeout=30)
                return ToolResult(True, str(r.json()))

            return ToolResult(False, "", f"Unknown: {action}")
        except Exception as e:
            return ToolResult(False, "", str(e))


def run(action: str = "list", **kwargs):
    return AirtableTool().run(action, **kwargs)