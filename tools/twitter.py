from httpx import AsyncClient
import os
import httpx


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


def run(action: str, **kwargs) -> str:
    """Synchronous dispatcher for Twitter API actions."""
    api_key = kwargs.get("api_key") or os.getenv("TWITTER_API_KEY")
    api_secret = kwargs.get("api_secret") or os.getenv("TWITTER_API_SECRET")
    access_token = kwargs.get("access_token") or os.getenv("TWITTER_ACCESS_TOKEN")
    access_secret = kwargs.get("access_secret") or os.getenv("TWITTER_ACCESS_SECRET")
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return _run_sync(action, kwargs)
        return loop.run_until_complete(_run_async(action, api_key, api_secret, access_token, access_secret, kwargs))
    except RuntimeError:
        return _run_sync(action, kwargs)


async def _run_async(action: str, api_key: str, api_secret: str, access_token: str, access_secret: str, kwargs: dict) -> str:
    """Async dispatcher for Twitter operations."""
    if action == "post_tweet":
        return str(await post_tweet(kwargs.get("text", ""), api_key, api_secret, access_token, access_secret))
    elif action == "get_tweet":
        return str(await get_tweet(kwargs.get("tweet_id", ""), api_key))
    elif action == "delete_tweet":
        return str(await delete_tweet(kwargs.get("tweet_id", ""), api_key))
    elif action == "search_tweets":
        return str(await search_tweets(kwargs.get("query", ""), api_key, kwargs.get("max_results", 10)))
    elif action == "get_user_tweets":
        return str(await get_user_tweets(kwargs.get("user_id", ""), api_key, kwargs.get("max_results", 10)))
    else:
        return f"Error: Unknown action '{action}'. Available: post_tweet, get_tweet, delete_tweet, search_tweets, get_user_tweets"


def _run_sync(action: str, kwargs: dict) -> str:
    """Synchronous fallback using httpx.Client."""
    api_key = kwargs.get("api_key") or os.getenv("TWITTER_API_KEY")
    api_secret = kwargs.get("api_secret") or os.getenv("TWITTER_API_SECRET")
    access_token = kwargs.get("access_token") or os.getenv("TWITTER_ACCESS_TOKEN")
    access_secret = kwargs.get("access_secret") or os.getenv("TWITTER_ACCESS_SECRET")
    try:
        client = httpx.Client(timeout=30)
        if action == "post_tweet":
            r = client.post("https://api.twitter.com/2/tweets",
                           json={"text": kwargs.get("text", "")}, auth=(api_key, api_secret))
            return str(r.json())[:2000]
        elif action == "get_tweet":
            r = client.get(f"https://api.twitter.com/2/tweets/{kwargs.get('tweet_id', '')}",
                          headers={"Authorization": f"Bearer {api_key}"})
            return str(r.json())[:2000]
        elif action == "delete_tweet":
            r = client.delete(f"https://api.twitter.com/2/tweets/{kwargs.get('tweet_id', '')}",
                             headers={"Authorization": f"Bearer {api_key}"})
            return str({"deleted": True})
        elif action == "search_tweets":
            r = client.get("https://api.twitter.com/2/tweets/search/recent",
                          params={"query": kwargs.get("query", ""), "max_results": kwargs.get("max_results", 10)},
                          headers={"Authorization": f"Bearer {api_key}"})
            return str(r.json())[:2000]
        elif action == "get_user_tweets":
            r = client.get(f"https://api.twitter.com/2/users/{kwargs.get('user_id', '')}/tweets",
                          params={"max_results": kwargs.get("max_results", 10)},
                          headers={"Authorization": f"Bearer {api_key}"})
            return str(r.json())[:2000]
        else:
            return f"Error: Unknown action '{action}'. Available: post_tweet, get_tweet, delete_tweet, search_tweets, get_user_tweets"
    except Exception as e:
        return f"Error: {str(e)}"