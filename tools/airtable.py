from tools.base import ToolResult
import httpx
import os

PLUGIN_NAME = "airtable"
PLUGIN_DESCRIPTION = "Airtable - collaborative bases"


def run(action: str = "list", **kwargs):
    token = os.getenv("AIRTABLE_API_TOKEN")
    if not token:
        return ToolResult(False, "", "Airtable token required. Set AIRTABLE_API_TOKEN environment variable.")

    base_id = kwargs.get("base_id") or os.getenv("AIRTABLE_BASE_ID")
    if not base_id:
        return ToolResult(False, "", "Airtable base_id required (pass base_id or set AIRTABLE_BASE_ID)")

    base_url = f"https://api.airtable.com/v0/{base_id}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        if action == "list":
            table = kwargs.get("table", "Table1")
            r = httpx.get(f"{base_url}/{table}", headers=headers, timeout=30)
            return ToolResult(r.status_code == 200, str(r.json()))

        if action == "create":
            table = kwargs.get("table", "Table1")
            fields = kwargs.get("fields", kwargs.get("data", {}))
            if not isinstance(fields, dict):
                return ToolResult(False, "", "fields must be an object")
            r = httpx.post(f"{base_url}/{table}", headers=headers, json={"fields": fields, "records": kwargs.get("records")}, timeout=30)
            return ToolResult(r.status_code in (200, 201), str(r.json()))

        return ToolResult(False, "", f"Unknown action: {action}. Available: list, create")
    except Exception as e:
        return ToolResult(False, "", str(e))