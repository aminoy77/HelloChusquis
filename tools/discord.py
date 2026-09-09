from httpx import AsyncClient
import os
import httpx

MAX_DISCORD_MEMBERS = 1000


def _member_limit(value: object) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return 20
    return max(1, min(limit, MAX_DISCORD_MEMBERS))


def run(action: str, **kwargs) -> str:
    """Synchronous dispatcher for Discord API actions."""
    token = kwargs.get("access_token") or os.getenv("DISCORD_BOT_TOKEN") or os.getenv("DISCORD_TOKEN")
    if not token:
        return "Error: No Discord token found. Set DISCORD_BOT_TOKEN environment variable."

    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return _run_sync(action, token, kwargs)
        return loop.run_until_complete(_run_async(action, token, kwargs))
    except RuntimeError:
        return _run_sync(action, token, kwargs)


async def _run_async(action: str, token: str, kwargs: dict) -> str:
    """Async dispatcher for Discord operations."""
    if action == "send_message":
        return await post_message(kwargs.get("channel_id", ""), kwargs.get("content", ""), token)
    elif action == "send_embed":
        return await post_message(kwargs.get("channel_id", ""), kwargs.get("content", ""), token)
    elif action == "create_channel":
        return await create_channel(kwargs.get("guild_id", ""), kwargs.get("name", ""), kwargs.get("type", 0), token)
    elif action == "list_channels":
        return await get_guild_members(kwargs.get("guild_id", ""), _member_limit(kwargs.get("limit", 20)), token)
    else:
        return f"Error: Unknown action '{action}'. Available: send_message, send_embed, create_channel, list_channels"


def _run_sync(action: str, token: str, kwargs: dict) -> str:
    """Synchronous fallback using httpx.Client."""
    base_url = "https://discord.com/api/v10"
    headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}

    try:
        client = httpx.Client(timeout=30)
        if action == "send_message":
            channel_id = kwargs.get("channel_id", "")
            r = client.post(f"{base_url}/channels/{channel_id}/messages", headers=headers,
                           json={"content": kwargs.get("content", "")})
            return str(r.json())[:2000]
        elif action == "send_embed":
            channel_id = kwargs.get("channel_id", "")
            r = client.post(f"{base_url}/channels/{channel_id}/messages", headers=headers,
                           json={"content": kwargs.get("content", "")})
            return str(r.json())[:2000]
        elif action == "create_channel":
            guild_id = kwargs.get("guild_id", "")
            r = client.post(f"{base_url}/guilds/{guild_id}/channels", headers=headers,
                           json={"name": kwargs.get("name", ""), "type": kwargs.get("type", 0)})
            return str(r.json())[:2000]
        elif action == "list_channels":
            guild_id = kwargs.get("guild_id", "")
            r = client.get(f"{base_url}/guilds/{guild_id}/channels", headers=headers)
            return str(r.json())[:2000]
        else:
            return f"Error: Unknown action '{action}'. Available: send_message, send_embed, create_channel, list_channels"
    except Exception as e:
        return f"Error: {str(e)}"


# --- Legacy async API (kept for backward compat) ---


async def post_message(group_id: str, message: str, access_token: str) -> dict:
    """Send message to Discord channel."""
    url = f"https://discord.com/api/v10/channels/{group_id}/messages"
    async with AsyncClient() as client:
        r = await client.post(url, json={"content": message}, headers={"Authorization": f"Bot {access_token}"})
        return r.json()


async def create_channel(guild_id: str, name: str, type: int, access_token: str) -> dict:
    """Create Discord channel."""
    url = f"https://discord.com/api/v10/guilds/{guild_id}/channels"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name, "type": type}, headers={"Authorization": f"Bot {access_token}"})
        return r.json()


async def get_channel(channel_id: str, access_token: str) -> dict:
    """Get Discord channel."""
    url = f"https://discord.com/api/v10/channels/{channel_id}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bot {access_token}"})
        return r.json()


async def add_reaction(channel_id: str, message_id: str, emoji: str, access_token: str) -> dict:
    """Add reaction to Discord message."""
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me"
    async with AsyncClient() as client:
        await client.put(url, headers={"Authorization": f"Bot {access_token}"})
        return {"reacted": True}


async def get_guild_members(guild_id: str, limit: int, access_token: str) -> dict:
    """Get Discord guild members."""
    url = f"https://discord.com/api/v10/guilds/{guild_id}/members"
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        r = await client.get(url, params={"limit": _member_limit(limit)}, headers={"Authorization": f"Bot {access_token}"})
        return r.json()