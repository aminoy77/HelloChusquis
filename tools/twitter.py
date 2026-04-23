from httpx import AsyncClient


async def post_tweet(text: str, api_key: str, api_secret: str, access_token: str, access_secret: str) -> dict:
    """Post tweet to Twitter/X."""
    url = "https://api.twitter.com/2/tweets"
    async with AsyncClient() as client:
        r = await client.post(url, json={"text": text}, auth=(api_key, api_secret))
        return r.json()


async def get_tweet(tweet_id: str, api_key: str) -> dict:
    """Get tweet from Twitter/X."""
    url = f"https://api.twitter.com/2/tweets/{tweet_id}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def delete_tweet(tweet_id: str, api_key: str) -> dict:
    """Delete tweet from Twitter/X."""
    url = f"https://api.twitter.com/2/tweets/{tweet_id}"
    async with AsyncClient() as client:
        r = await client.delete(url, headers={"Authorization": f"Bearer {api_key}"})
        return {"deleted": True}


async def search_tweets(query: str, api_key: str, max_results: int = 10) -> dict:
    """Search tweets."""
    url = f"https://api.twitter.com/2/tweets/search/recent"
    async with AsyncClient() as client:
        r = await client.get(url, params={"query": query, "max_results": max_results}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def get_user_tweets(user_id: str, api_key: str, max_results: int = 10) -> dict:
    """Get user tweets."""
    url = f"https://api.twitter.com/2/users/{user_id}/tweets"
    async with AsyncClient() as client:
        r = await client.get(url, params={"max_results": max_results}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()