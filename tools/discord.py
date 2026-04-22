from tools.base import BaseTool, ToolResult
import httpx
import os


PLUGIN_NAME = "discord"
PLUGIN_DESCRIPTION = "Send messages to Discord channels via webhooks"

DISCORD_SCHEMA = {
    "type": "function",
    "function": {
        "name": "discord",
        "description": "Send messages to Discord channels via webhook",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["send_message", "send_embed"],
                    "description": "The Discord action to perform"
                },
                "webhook_url": {"type": "string", "description": "Discord webhook URL"},
                "channel_id": {"type": "string", "description": "Channel ID for preset webhooks"},
                "content": {"type": "string", "description": "Message content to send"},
                "username": {"type": "string", "description": "Custom username for the bot"},
                "avatar_url": {"type": "string", "description": "Custom avatar URL"},
                "title": {"type": "string", "description": "Embed title"},
                "description": {"type": "string", "description": "Embed description"},
                "color": {"type": "string", "description": "Embed color (hex, e.g., 00ff00)"},
                "url": {"type": "string", "description": "Link for title in embed"},
            },
            "required": ["action"]
        }
    }
}


def get_discord_webhook() -> str:
    """Get Discord webhook URL from environment."""
    return os.getenv("DISCORD_WEBHOOK_URL") or os.getenv("DISCORD_WEBHOOK")


def run(action: str, webhook_url: str = "", channel_id: str = "", content: str = "",
       username: str = "HelloChusquis", avatar_url: str = "",
       title: str = "", description: str = "", color: str = "", url: str = "") -> str:
    """Execute Discord webhook actions."""
    
    # Get webhook from env if not provided
    if not webhook_url:
        webhook_url = get_discord_webhook()
        if not webhook_url:
            return "Error: No Discord webhook found. Set DISCORD_WEBHOOK_URL or provide webhook_url."
    
    # Get preset webhook from channel_id
    if channel_id and not webhook_url:
        preset_webhooks = {
            "alerts": os.getenv("DISCORD_WEBHOOK_ALERTS"),
            "logs": os.getenv("DISCORD_WEBHOOK_LOGS"),
            "general": os.getenv("DISCORD_WEBHOOK_GENERAL"),
        }
        webhook_url = preset_webhooks.get(channel_id.lower())
        if not webhook_url:
            # Try to construct webhook URL ( Bot token needed for this method)
            bot_token = os.getenv("DISCORD_BOT_TOKEN")
            if bot_token:
                # This would need additional API calls to create webhook
                return "Error: Need webhook URL or configure preset channels."
            return "Error: No webhook configured for this channel."
    
    try:
        client = httpx.Client(timeout=30)
        
        if action == "send_message":
            if not content:
                return "Error: content required for send_message"
            
            payload = {
                "content": content,
                "username": username
            }
            if avatar_url:
                payload["avatar_url"] = avatar_url
            
            resp = client.post(webhook_url, json=payload)
            if resp.status_code in [200, 204]:
                return f"Message sent to Discord! :white_check_mark:"
            return f"Error: {resp.status_code} - {resp.text[:200]}"
        
        elif action == "send_embed":
            if not content and not description:
                return "Error: content or description required for send_embed"
            
            # Parse color (hex to decimal)
            color_value = 0
            if color:
                try:
                    color_value = int(color.replace("#", ""), 16)
                except:
                    color_value = 0
            
            embed = {
                "title": title,
                "description": description or content,
                "color": color_value
            }
            if url:
                embed["url"] = url
            
            payload = {
                "embeds": [embed],
                "username": username
            }
            if avatar_url:
                payload["avatar_url"] = avatar_url
            
            resp = client.post(webhook_url, json=payload)
            if resp.status_code in [200, 204]:
                return f"Embed message sent to Discord! :white_check_mark:"
            return f"Error: {resp.status_code} - {resp.text[:200]}"
        
        else:
            return f"Error: Unknown action '{action}'. Available: send_message, send_embed"
    
    except httpx.TimeoutException:
        return "Error: Request timed out after 30 seconds."
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    print("Discord plugin loaded. Use 'discord' tool in HelloChusquis.")