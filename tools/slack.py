from tools.base import BaseTool, ToolResult
import httpx
import os


PLUGIN_NAME = "slack"
PLUGIN_DESCRIPTION = "Send messages to Slack channels and users"

SLACK_SCHEMA = {
    "type": "function",
    "function": {
        "name": "slack",
        "description": "Send messages to Slack channels or users",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["post_message", "list_channels", "get_channel", "list_users"],
                    "description": "The Slack action to perform"
                },
                "channel": {"type": "string", "description": "Channel name or ID (e.g., #general)"},
                "user": {"type": "string", "description": "User name or ID"},
                "text": {"type": "string", "description": "Message text to send"},
                "username": {"type": "string", "description": "Custom bot username (default: HelloChusquis)"},
                "icon_emoji": {"type": "string", "description": "Emoji icon (e.g., :robot_face:)"},
            },
            "required": ["action"]
        }
    }
}


def get_slack_token() -> str:
    """Get Slack token from environment."""
    return os.getenv("SLACK_BOT_TOKEN") or os.getenv("SLACK_TOKEN")


def get_slack_config() -> dict:
    """Get Slack configuration."""
    return {
        "token": get_slack_token(),
        "signing_secret": os.getenv("SLACK_SIGNING_SECRET"),
        "app_id": os.getenv("SLACK_APP_ID")
    }


def run(action: str, channel: str = "", user: str = "", text: str = "", 
       username: str = "HelloChusquis", icon_emoji: str = ":robot_face:") -> str:
    """Execute Slack API actions."""
    token = get_slack_token()
    if not token:
        return "Error: No Slack token found. Set SLACK_BOT_TOKEN environment variable."
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    base_url = "https://slack.com/api"
    
    try:
        client = httpx.Client(timeout=30)
        
        if action == "list_channels":
            resp = client.get(f"{base_url}/conversations.list", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    channels = data.get("channels", [])[:20]
                    result = []
                    for c in channels:
                        members = c.get("member_count", 0)
                        result.append(f"• #{c.get('name')} (ID: {c.get('id')}) - {members} members")
                    return "\n".join(result) if result else "No channels found."
                return f"Error: {data.get('error', 'Unknown error')}"
            return f"Error: {resp.status_code}"
        
        elif action == "get_channel":
            if not channel:
                return "Error: channel name or ID required for get_channel"
            channel_id = channel.lstrip("#")
            resp = client.get(f"{base_url}/conversations.info?channel={channel_id}", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    c = data.get("channel", {})
                    return f"Channel: #{c.get('name')}\nID: {c.get('id')}\nMembers: {c.get('member_count')}\nTopic: {c.get('topic', {}).get('value', 'N/A')}"
                return f"Error: {data.get('error', 'Unknown error')}"
            return f"Error: {resp.status_code}"
        
        elif action == "list_users":
            resp = client.get(f"{base_url}/users.list", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    members = data.get("members", [])[:20]
                    result = []
                    for m in members:
                        status = m.get("profile", {}).get("status_text", "")
                        result.append(f"• @{m.get('name')} ({m.get('real_name', 'N/A')}) {status}")
                    return "\n".join(result) if result else "No users found."
                return f"Error: {data.get('error', 'Unknown error')}"
            return f"Error: {resp.status_code}"
        
        elif action == "post_message":
            if not channel or not text:
                return "Error: channel and text required for post_message"
            
            # Clean channel name
            channel_id = channel.lstrip("#")
            
            payload = {
                "channel": channel_id,
                "text": text,
                "username": username,
                "icon_emoji": icon_emoji
            }
            
            resp = client.post(f"{base_url}/chat.postMessage", headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    ts = data.get("ts")
                    return f"Message sent to #{channel_id}! :white_check_mark:\nTimestamp: {ts}"
                return f"Error: {data.get('error', 'Unknown error')}"
            return f"Error: {resp.status_code} - {resp.text}"
        
        else:
            return f"Error: Unknown action '{action}'. Available: post_message, list_channels, get_channel, list_users"
    
    except httpx.TimeoutException:
        return "Error: Request timed out after 30 seconds."
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    print("Slack plugin loaded. Use 'slack' tool in HelloChusquis.")