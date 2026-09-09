"""Slack integration with bounded, non-redirecting HTTP requests."""

from __future__ import annotations

import os

import httpx

PLUGIN_NAME = "slack"
PLUGIN_DESCRIPTION = "Send messages to Slack channels and users"
MAX_SLACK_RESULTS = 100
MAX_SLACK_MESSAGE_CHARS = 40_000
MAX_SLACK_CHANNEL_CHARS = 255

SLACK_SCHEMA = {
    "type": "function",
    "function": {
        "name": "slack",
        "description": "Send messages to Slack channels or users",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["post_message", "list_channels", "get_channel", "list_users"]},
                "channel": {"type": "string", "description": "Channel name or ID (e.g., #general)"},
                "user": {"type": "string", "description": "User name or ID"},
                "text": {"type": "string", "description": "Message text to send"},
                "username": {"type": "string", "description": "Custom bot username"},
                "icon_emoji": {"type": "string", "description": "Emoji icon"},
            },
            "required": ["action"],
        },
    },
}


def get_slack_token() -> str:
    """Get Slack token from environment."""
    return os.getenv("SLACK_BOT_TOKEN") or os.getenv("SLACK_TOKEN") or ""


def get_slack_config() -> dict:
    """Get Slack configuration without exposing it in responses."""
    return {
        "token": get_slack_token(),
        "signing_secret": os.getenv("SLACK_SIGNING_SECRET"),
        "app_id": os.getenv("SLACK_APP_ID"),
    }


def _channel_id(channel: object) -> str | None:
    identifier = str(channel or "").lstrip("#")
    if not identifier or len(identifier) > MAX_SLACK_CHANNEL_CHARS or "\x00" in identifier:
        return None
    return identifier


def _api_error(response: httpx.Response) -> str:
    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text[:500]}"
    try:
        return str(response.json().get("error", "Unknown error"))
    except ValueError:
        return "Unknown error"


def run(
    action: str,
    channel: str = "",
    user: str = "",
    text: str = "",
    username: str = "HelloChusquis",
    icon_emoji: str = ":robot_face:",
) -> str:
    """Execute bounded Slack API actions."""
    del user  # Reserved by the public schema for future direct-message support.
    token = get_slack_token()
    if not token:
        return "Error: No Slack token found. Set SLACK_BOT_TOKEN environment variable."

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"}
    base_url = "https://slack.com/api"
    client = httpx.Client(timeout=30, follow_redirects=False)
    try:
        if action == "list_channels":
            response = client.get(f"{base_url}/conversations.list", headers=headers, params={"limit": MAX_SLACK_RESULTS})
            if response.status_code != 200:
                return _api_error(response)
            data = response.json()
            if not data.get("ok"):
                return f"Error: {data.get('error', 'Unknown error')}"
            channels = data.get("channels", [])[:MAX_SLACK_RESULTS]
            result = [f"• #{item.get('name')} (ID: {item.get('id')}) - {item.get('member_count', 0)} members" for item in channels]
            return "\n".join(result) if result else "No channels found."

        if action == "get_channel":
            channel_id = _channel_id(channel)
            if not channel_id:
                return "Error: valid channel name or ID required for get_channel"
            response = client.get(
                f"{base_url}/conversations.info",
                headers=headers,
                params={"channel": channel_id},
            )
            if response.status_code != 200:
                return _api_error(response)
            data = response.json()
            if not data.get("ok"):
                return f"Error: {data.get('error', 'Unknown error')}"
            found = data.get("channel", {})
            return (
                f"Channel: #{found.get('name')}\nID: {found.get('id')}\n"
                f"Members: {found.get('member_count')}\nTopic: {found.get('topic', {}).get('value', 'N/A')}"
            )

        if action == "list_users":
            response = client.get(f"{base_url}/users.list", headers=headers, params={"limit": MAX_SLACK_RESULTS})
            if response.status_code != 200:
                return _api_error(response)
            data = response.json()
            if not data.get("ok"):
                return f"Error: {data.get('error', 'Unknown error')}"
            members = data.get("members", [])[:MAX_SLACK_RESULTS]
            result = [
                f"• @{member.get('name')} ({member.get('real_name', 'N/A')}) {member.get('profile', {}).get('status_text', '')}"
                for member in members
            ]
            return "\n".join(result) if result else "No users found."

        if action == "post_message":
            channel_id = _channel_id(channel)
            if not channel_id or not isinstance(text, str) or not text:
                return "Error: valid channel and text required for post_message"
            if len(text) > MAX_SLACK_MESSAGE_CHARS:
                return f"Error: message exceeds {MAX_SLACK_MESSAGE_CHARS} characters."
            payload = {"channel": channel_id, "text": text, "username": str(username)[:80], "icon_emoji": str(icon_emoji)[:100]}
            response = client.post(f"{base_url}/chat.postMessage", headers=headers, json=payload)
            if response.status_code != 200:
                return _api_error(response)
            data = response.json()
            if data.get("ok"):
                return f"Message sent to #{channel_id}.\nTimestamp: {data.get('ts')}"
            return f"Error: {data.get('error', 'Unknown error')}"

        return "Error: Unknown action. Available: post_message, list_channels, get_channel, list_users"
    except httpx.TimeoutException:
        return "Error: Request timed out after 30 seconds."
    except httpx.HTTPError as exc:
        return f"Error: {exc}"
    except ValueError:
        return "Error: Slack returned an invalid JSON response."
    finally:
        client.close()
