"""Safe Twitter/X API v2 integration."""

from __future__ import annotations

import asyncio
import os
import re
from typing import Any

import httpx


_BASE_URL = "https://api.twitter.com/2"
_TWITTER_ID_RE = re.compile(r"[1-9][0-9]{0,19}")


def _twitter_id(value: object) -> str:
    """Validate a numeric Twitter resource identifier before placing it in a path."""
    identifier = str(value or "").strip()
    if not _TWITTER_ID_RE.fullmatch(identifier):
        raise ValueError("Twitter resource identifier must be a positive numeric identifier.")
    return identifier


def _bounded_max_results(value: object, default: int = 10) -> int:
    try:
        max_results = int(value)
    except (TypeError, ValueError):
        max_results = default
    return max(10, min(max_results, 100))


def _tweet_text(value: object) -> str:
    text = str(value or "")
    if not text.strip() or len(text) > 280 or "\x00" in text:
        raise ValueError("Tweet text must contain 1 to 280 characters and no null bytes.")
    return text


def _bearer_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _request(
    method: str,
    path: str,
    token: str,
    *,
    json_data: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    expect_json: bool = True,
) -> dict[str, Any]:
    """Perform a bounded Twitter API request without following redirects."""
    async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.request(
            method,
            f"{_BASE_URL}{path}",
            json=json_data,
            params=params,
            headers=_bearer_headers(token),
        )
        if expect_json:
            return response.json()
        return {"deleted": response.is_success}


async def post_tweet(
    text: str,
    api_key: str,
    api_secret: str,
    access_token: str,
    access_secret: str,
) -> dict[str, Any]:
    """Post a tweet using a user access token; app credentials cannot post on behalf of a user."""
    del api_key, api_secret, access_secret
    if not access_token:
        raise ValueError("A Twitter user access token is required to post a tweet.")
    return await _request("POST", "/tweets", access_token, json_data={"text": _tweet_text(text)})


async def get_tweet(tweet_id: str, api_key: str) -> dict[str, Any]:
    """Get a tweet selected by a validated numeric identifier."""
    return await _request("GET", f"/tweets/{_twitter_id(tweet_id)}", api_key)


async def delete_tweet(tweet_id: str, api_key: str) -> dict[str, Any]:
    """Delete a tweet using a user access token."""
    if not api_key:
        raise ValueError("A Twitter user access token is required to delete a tweet.")
    return await _request("DELETE", f"/tweets/{_twitter_id(tweet_id)}", api_key, expect_json=False)


async def search_tweets(query: str, api_key: str, max_results: int = 10) -> dict[str, Any]:
    """Search recent tweets using structured parameters and a bounded result count."""
    clean_query = str(query or "").strip()
    if not clean_query or len(clean_query) > 4096 or any(char in clean_query for char in "\r\n\x00"):
        raise ValueError("query must be non-empty and cannot contain control characters.")
    return await _request(
        "GET",
        "/tweets/search/recent",
        api_key,
        params={"query": clean_query, "max_results": _bounded_max_results(max_results)},
    )


async def get_user_tweets(user_id: str, api_key: str, max_results: int = 10) -> dict[str, Any]:
    """Get a bounded set of tweets for a validated user identifier."""
    return await _request(
        "GET",
        f"/users/{_twitter_id(user_id)}/tweets",
        api_key,
        params={"max_results": _bounded_max_results(max_results)},
    )


def run(action: str, **kwargs: Any) -> str:
    """Synchronous dispatcher for Twitter API actions."""
    api_key = kwargs.get("api_key") or os.getenv("TWITTER_API_KEY")
    api_secret = kwargs.get("api_secret") or os.getenv("TWITTER_API_SECRET")
    access_token = kwargs.get("access_token") or os.getenv("TWITTER_ACCESS_TOKEN")
    access_secret = kwargs.get("access_secret") or os.getenv("TWITTER_ACCESS_SECRET")
    read_token = str(api_key or "")
    write_token = str(access_token or "")

    if action in {"post_tweet", "delete_tweet"} and not write_token:
        return "Error: A Twitter user access token is required for this action. Set TWITTER_ACCESS_TOKEN."
    if action not in {"post_tweet", "delete_tweet"} and not read_token:
        return "Error: No Twitter API bearer token found. Set TWITTER_API_KEY."

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return _run_sync(action, kwargs, read_token, write_token)
        return loop.run_until_complete(
            _run_async(action, read_token, str(api_secret or ""), write_token, str(access_secret or ""), kwargs)
        )
    except RuntimeError:
        return _run_sync(action, kwargs, read_token, write_token)


async def _run_async(
    action: str,
    read_token: str,
    api_secret: str,
    write_token: str,
    access_secret: str,
    kwargs: dict[str, Any],
) -> str:
    """Async dispatcher for Twitter operations."""
    if action == "post_tweet":
        result = await post_tweet(kwargs.get("text", ""), read_token, api_secret, write_token, access_secret)
    elif action == "get_tweet":
        result = await get_tweet(kwargs.get("tweet_id", ""), read_token)
    elif action == "delete_tweet":
        result = await delete_tweet(kwargs.get("tweet_id", ""), write_token)
    elif action == "search_tweets":
        result = await search_tweets(kwargs.get("query", ""), read_token, kwargs.get("max_results", 10))
    elif action == "get_user_tweets":
        result = await get_user_tweets(kwargs.get("user_id", ""), read_token, kwargs.get("max_results", 10))
    else:
        return "Error: Unknown action '{}'. Available: post_tweet, get_tweet, delete_tweet, search_tweets, get_user_tweets".format(action)
    return str(result)[:2000]


def _run_sync(action: str, kwargs: dict[str, Any], read_token: str, write_token: str) -> str:
    """Synchronous fallback using an explicit timeout and redirect protection."""
    try:
        with httpx.Client(timeout=30, follow_redirects=False) as client:
            if action == "post_tweet":
                response = client.post(
                    f"{_BASE_URL}/tweets",
                    json={"text": _tweet_text(kwargs.get("text", ""))},
                    headers=_bearer_headers(write_token),
                )
            elif action == "get_tweet":
                response = client.get(
                    f"{_BASE_URL}/tweets/{_twitter_id(kwargs.get('tweet_id', ''))}",
                    headers=_bearer_headers(read_token),
                )
            elif action == "delete_tweet":
                response = client.delete(
                    f"{_BASE_URL}/tweets/{_twitter_id(kwargs.get('tweet_id', ''))}",
                    headers=_bearer_headers(write_token),
                )
                return str({"deleted": response.is_success})[:2000]
            elif action == "search_tweets":
                query = str(kwargs.get("query", "")).strip()
                if not query or len(query) > 4096 or any(char in query for char in "\r\n\x00"):
                    raise ValueError("query must be non-empty and cannot contain control characters.")
                response = client.get(
                    f"{_BASE_URL}/tweets/search/recent",
                    params={"query": query, "max_results": _bounded_max_results(kwargs.get("max_results", 10))},
                    headers=_bearer_headers(read_token),
                )
            elif action == "get_user_tweets":
                response = client.get(
                    f"{_BASE_URL}/users/{_twitter_id(kwargs.get('user_id', ''))}/tweets",
                    params={"max_results": _bounded_max_results(kwargs.get("max_results", 10))},
                    headers=_bearer_headers(read_token),
                )
            else:
                return "Error: Unknown action '{}'. Available: post_tweet, get_tweet, delete_tweet, search_tweets, get_user_tweets".format(action)
            return str(response.json())[:2000]
    except (ValueError, httpx.HTTPError) as exc:
        return f"Error: {exc}"
