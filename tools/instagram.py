from httpx import AsyncClient


async def post_media(media_url: str, caption: str, api_key: str) -> dict:
    """Post media to Instagram."""
    url = "https://graph.facebook.com/v18.0/me/media"
    async with AsyncClient() as client:
        r = await client.post(url, json={
            "media_type": "IMAGE",
            "image_url": media_url,
            "caption": caption
        }, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def publish_media(creation_id: str, api_key: str) -> dict:
    """Publish Instagram media."""
    url = "https://graph.facebook.com/v18.0/me/media_publish"
    async with AsyncClient() as client:
        r = await client.post(url, json={"creation_id": creation_id}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def get_media(api_key: str, limit: int = 10) -> dict:
    """Get Instagram media."""
    url = f"https://graph.facebook.com/v18.0/me/media?limit={limit}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def get_insights(media_id: str, api_key: str) -> dict:
    """Get Instagram media insights."""
    url = f"https://graph.facebook.com/v18.0/{media_id}/insights"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def get_user_insights(api_key: str) -> dict:
    """Get Instagram user insights."""
    url = "https://graph.facebook.com/v18.0/me/insights"
    async with AsyncClient() as client:
        r = await client.get(url, params={"metric": "impressions,reach,follower_count"}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()