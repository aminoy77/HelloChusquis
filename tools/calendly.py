from tools.base import ToolResult
import httpx
import os

PLUGIN_NAME = "calendly"
PLUGIN_DESCRIPTION = "Calendly meeting scheduling"


def run(action: str = "list", **kwargs):
    token = os.getenv("CALENDLY_API_TOKEN")
    if not token:
        return ToolResult(False, "", "Calendly token required. Set CALENDLY_API_TOKEN environment variable.")

    headers = {"Authorization": f"Bearer {token}"}

    try:
        if action == "list_events":
            user_uri = kwargs.get("user", os.getenv("CALENDLY_USER_URI"))
            params = {}
            if user_uri:
                params["user"] = user_uri
            r = httpx.get("https://api.calendly.com/scheduled_events", headers=headers, params=params, timeout=30)
            return ToolResult(r.status_code == 200, str(r.json()))

        if action == "get_user":
            r = httpx.get("https://api.calendly.com/users/me", headers=headers, timeout=30)
            return ToolResult(r.status_code == 200, str(r.json()))

        if action == "list_event_types":
            user_uri = kwargs.get("user", os.getenv("CALENDLY_USER_URI"))
            if not user_uri:
                return ToolResult(False, "", "user (URI) required for list_event_types or set CALENDLY_USER_URI")
            r = httpx.get("https://api.calendly.com/event_types", headers=headers, params={"user": user_uri}, timeout=30)
            return ToolResult(r.status_code == 200, str(r.json()))

        return ToolResult(False, "", f"Unknown action: {action}. Available: list_events, get_user, list_event_types")
    except Exception as e:
        return ToolResult(False, "", str(e))