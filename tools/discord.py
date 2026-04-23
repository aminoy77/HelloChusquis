from httpx import AsyncClient


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
        r = await client.put(url, headers={"Authorization": f"Bot {access_token}"})
        return {"reacted": True}


async def get_guild_members(guild_id: str, limit: int, access_token: str) -> dict:
    """Get Discord guild members."""
    url = f"https://discord.com/api/v10/guilds/{guild_id}/members?limit={limit}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bot {access_token}"})
        return r.json()