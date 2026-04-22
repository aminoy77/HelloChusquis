from tools.base import BaseTool, ToolResult
import httpx
import os
import json


PLUGIN_NAME = "twitter"
PLUGIN_DESCRIPTION = "Post tweets and interact with Twitter/X API"

TWITTER_SCHEMA = {
    "type": "function",
    "function": {
        "name": "twitter",
        "description": "Post tweets, get user info, and search Twitter",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["post_tweet", "get_user", "search_tweets", "get_timeline", "get_mentions"],
                    "description": "The Twitter action to perform"
                },
                "text": {"type": "string", "description": "Tweet text (max 280 chars)"},
                "username": {"type": "string", "description": "Twitter username"},
                "query": {"type": "string", "description": "Search query"},
                "count": {"type": "number", "description": "Number of results (default 10)"},
                "reply_to": {"type": "string", "description": "Tweet ID to reply to"},
            },
            "required": ["action"]
        }
    }
}


def get_twitter_credentials() -> dict:
    """Get Twitter credentials from environment."""
    return {
        "api_key": os.getenv("TWITTER_API_KEY"),
        "api_secret": os.getenv("TWITTER_API_SECRET"),
        "access_token": os.getenv("TWITTER_ACCESS_TOKEN"),
        "access_secret": os.getenv("TWITTER_ACCESS_SECRET"),
    }


def get_bearer_token(creds: dict) -> str:
    """Get OAuth 2 Bearer token for API v2."""
    return os.getenv("TWITTER_BEARER_TOKEN") or creds.get("access_token", "")


def run(action: str, text: str = "", username: str = "", query: str = "", count: int = 10, reply_to: str = "") -> str:
    """Execute Twitter API actions."""
    creds = get_twitter_credentials()
    bearer = get_bearer_token(creds)
    
    if not bearer:
        # Try to get from environment directly
        bearer = os.getenv("TWITTER_BEARER_TOKEN")
    
    if not bearer:
        return "Error: Twitter credentials not found. Set TWITTER_BEARER_TOKEN or TWITTER_ACCESS_TOKEN."
    
    headers = {
        "Authorization": f"Bearer {bearer}",
        "Content-Type": "application/json"
    }
    
    base_url = "https://api.twitter.com/2"
    
    try:
        client = httpx.Client(timeout=30)
        
        if action == "get_user":
            if not username:
                return "Error: username required for get_user"
            # Remove @ if present
            username = username.lstrip("@")
            resp = client.get(f"{base_url}/users/by/username/{username}", headers=headers)
            if resp.status_code == 200:
                user = resp.json().get("data", {})
                return f"@{user.get('username')}\nName: {user.get('name')}\nFollowers: {user.get('public_metrics', {}).get('followers_count', 'N/A')}\nFollowing: {user.get('public_metrics', {}).get('following_count', 'N/A')}\nTweets: {user.get('public_metrics', {}).get('tweet_count', 'N/A')}"
            return f"Error: {resp.status_code} - {resp.text[:200]}"
        
        elif action == "post_tweet":
            if not text:
                return "Error: text required for post_tweet"
            
            if len(text) > 280:
                text = text[:277] + "..."
            
            payload = {"text": text}
            if reply_to:
                payload["reply"] = {"in_reply_to_tweet_id": reply_to}
            
            # Need user context - requires OAuth 1.0a or OAuth 2.0 with write permissions
            access_token = creds.get("access_token") or os.getenv("TWITTER_ACCESS_TOKEN")
            if not access_token:
                return "Error: Posting tweets requires OAuth access token. Use TWITTER_ACCESS_TOKEN."
            
            # Get user ID first
            user_resp = client.get(f"{base_url}/users/me", headers={"Authorization": f"Bearer {bearer}"})
            if user_resp.status_code != 200:
                return "Error: Could not get user info. Check credentials."
            
            user_id = user_resp.json().get("data", {}).get("id")
            if not user_id:
                return "Error: Could not determine user ID."
            
            # Post tweet
            resp = client.post(f"{base_url}/users/{user_id}/tweets", headers=headers, json=payload)
            if resp.status_code == 201:
                tweet = resp.json().get("data", {})
                return f"Tweet posted! :white_check_mark:\nID: {tweet.get('id')}\nhttps://twitter.com/i/status/{tweet.get('id')}"
            return f"Error: {resp.status_code} - {resp.text[:200]}"
        
        elif action == "search_tweets":
            if not query:
                return "Error: query required for search_tweets"
            
            resp = client.get(f"{base_url}/tweets/search/recent", headers=headers, params={"query": query, "max_results": count})
            if resp.status_code == 200:
                tweets = resp.json().get("data", [])
                result = []
                for t in tweets:
                    result.append(f"• @{t.get('author_id', 'N/A')}: {t.get('text', 'N/A')[:100]}")
                return "\n".join(result) if result else "No tweets found."
            return f"Error: {resp.status_code} - {resp.text[:200]}"
        
        elif action == "get_timeline":
            access_token = creds.get("access_token") or os.getenv("TWITTER_ACCESS_TOKEN")
            if not access_token:
                return "Error: Getting timeline requires access token."
            
            # Get user ID
            user_resp = client.get(f"{base_url}/users/me", headers={"Authorization": f"Bearer {bearer}"})
            if user_resp.status_code != 200:
                return "Error: Could not get user info."
            
            user_id = user_resp.json().get("data", {}).get("id")
            resp = client.get(f"{base_url}/users/{user_id}/tweets", headers=headers, params={"max_results": count})
            if resp.status_code == 200:
                tweets = resp.json().get("data", [])
                result = []
                for t in tweets:
                    result.append(f"• {t.get('text', 'N/A')[:100]}")
                return "\n".join(result) if result else "No tweets found."
            return f"Error: {resp.status_code} - {resp.text[:200]}"
        
        elif action == "get_mentions":
            access_token = creds.get("access_token") or os.getenv("TWITTER_ACCESS_TOKEN")
            if not access_token:
                return "Error: Getting mentions requires access token."
            
            # Get user ID
            user_resp = client.get(f"{base_url}/users/me", headers={"Authorization": f"Bearer {bearer}"})
            if user_resp.status_code != 200:
                return "Error: Could not get user info."
            
            user_id = user_resp.json().get("data", {}).get("id")
            resp = client.get(f"{base_url}/users/{user_id}/mentions", headers=headers, params={"max_results": count})
            if resp.status_code == 200:
                tweets = resp.json().get("data", [])
                result = []
                for t in tweets:
                    result.append(f"• @{t.get('author_id', 'N/A')}: {t.get('text', 'N/A')[:100]}")
                return "\n".join(result) if result else "No mentions found."
            return f"Error: {resp.status_code} - {resp.text[:200]}"
        
        else:
            return f"Error: Unknown action '{action}'. Available: post_tweet, get_user, search_tweets, get_timeline, get_mentions"
    
    except httpx.TimeoutException:
        return "Error: Request timed out after 30 seconds."
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    print("Twitter plugin loaded. Use 'twitter' tool in HelloChusquis.")