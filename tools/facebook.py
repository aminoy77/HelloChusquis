from httpx import AsyncClient


async def create_page(name: str, access_token: str) -> dict:
    """Create Facebook page."""
    url = "https://graph.facebook.com/v18.0/me/accounts"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name}, headers={"Authorization": f"Bearer {access_token}"})
        return r.json()


async def post_to_page(page_id: str, message: str, access_token: str) -> dict:
    """Post to Facebook page."""
    url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
    async with AsyncClient() as client:
        r = await client.post(url, json={"message": message}, headers={"Authorization": f"Bearer {access_token}"})
        return r.json()


async def get_page_insights(page_id: str, access_token: str) -> dict:
    """Get Facebook page insights."""
    url = f"https://graph.facebook.com/v18.0/{page_id}/insights"
    async with AsyncClient() as client:
        r = await client.get(url, params={"metric": "page_fans,page_impressions"}, headers={"Authorization": f"Bearer {access_token}"})
        return r.json()


async def send_message(recipient_id: str, message: str, access_token: str) -> dict:
    """Send Facebook message."""
    url = "https://graph.facebook.com/v18.0/me/messages"
    async with AsyncClient() as client:
        r = await client.post(url, json={"recipient": {"id": recipient_id}, "message": {"text": message}}, headers={"Authorization": f"Bearer {access_token}"})
        return r.json()