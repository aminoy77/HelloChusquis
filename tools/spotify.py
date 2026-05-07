from tools.base import BaseTool, ToolResult
import httpx
import os
import json


PLUGIN_NAME = "spotify"
PLUGIN_DESCRIPTION = "Control Spotify playback and manage playlists"

SPOTIFY_SCHEMA = {
    "type": "function",
    "function": {
        "name": "spotify",
        "description": "Control Spotify playback and manage playlists",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["play", "pause", "next", "previous", "search", "play_playlist", "currently_playing", "get_playlists"],
                    "description": "The Spotify action to perform"
                },
                "query": {"type": "string", "description": "Search query or playlist name"},
                "playlist_id": {"type": "string", "description": "Spotify playlist ID"},
                "track_uri": {"type": "string", "description": " Spotify track URI"},
                "device_id": {"type": "string", "description": "Device ID"},
                "limit": {"type": "number", "description": "Number of results (default 10)"},
            },
            "required": ["action"]
        }
    }
}


def get_spotify_credentials() -> dict:
    """Get Spotify credentials from environment."""
    return {
        "client_id": os.getenv("SPOTIFY_CLIENT_ID"),
        "client_secret": os.getenv("SPOTIFY_CLIENT_SECRET"),
        "access_token": os.getenv("SPOTIFY_ACCESS_TOKEN"),
    }


def get_access_token(creds: dict) -> str:
    """Get or refresh access token."""
    if creds["access_token"]:
        return creds["access_token"]
    
    # Would need to implement OAuth flow here
    return ""


def run(action: str, query: str = "", playlist_id: str = "", track_uri: str = "",
       device_id: str = "", limit: int = 10) -> str:
    """Execute Spotify API actions."""
    creds = get_spotify_credentials()
    token = get_access_token(creds)
    
    if not token:
        token = os.getenv("SPOTIFY_ACCESS_TOKEN")
    
    if not token:
        # Try to get from cache/file
        token_file = os.path.expanduser("~/.spotify_token")
        if os.path.exists(token_file):
            with open(token_file) as f:
                token = f.read().strip()
    
    if not token:
        return "Error: Spotify token not found. Set SPOTIFY_ACCESS_TOKEN."
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    base_url = "https://api.spotify.com/v1"

    try:
        with httpx.Client(timeout=30) as client:
            if action == "currently_playing":
                resp = client.get(f"{base_url}/me/player/currently-playing", headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if data:
                        item = data.get("item", {})
                        return f"Now playing: {item.get('name', 'N/A')}\nArtist: {item.get('artists', [{}])[0].get('name', 'N/A')}\nAlbum: {item.get('album', {}).get('name', 'N/A')}"
                    return "Nothing playing."
                return f"Error: {resp.status_code} - {resp.text[:200]}"

            elif action == "play":
                payload = {}
                if track_uri:
                    payload["uris"] = [track_uri]
                elif playlist_id:
                    payload["context_uri"] = f"spotify:playlist:{playlist_id}"
                resp = client.put(f"{base_url}/me/player/play", headers=headers, json=payload if payload else None)
                if resp.status_code in [200, 204]:
                    return "Playing! :white_check_mark:"
                return f"Error: {resp.status_code} - {resp.text[:200]}"

            elif action == "pause":
                resp = client.put(f"{base_url}/me/player/pause", headers=headers)
                if resp.status_code in [200, 204]:
                    return "Paused! :white_check_mark:"
                return f"Error: {resp.status_code} - {resp.text[:200]}"

            elif action == "next":
                resp = client.post(f"{base_url}/me/player/next", headers=headers)
                if resp.status_code in [200, 204]:
                    return "Skipped to next track! :white_check_mark:"
                return f"Error: {resp.status_code} - {resp.text[:200]}"

            elif action == "previous":
                resp = client.post(f"{base_url}/me/player/previous", headers=headers)
                if resp.status_code in [200, 204]:
                    return "Went to previous track! :white_check_mark:"
                return f"Error: {resp.status_code} - {resp.text[:200]}"

            elif action == "search":
                if not query:
                    return "Error: query required for search"
                resp = client.get(f"{base_url}/search", headers=headers, params={"q": query, "type": "track", "limit": limit})
                if resp.status_code == 200:
                    tracks = resp.json().get("tracks", {}).get("items", [])
                    result = []
                    for t in tracks:
                        artists = ", ".join([a.get("name", "N/A") for a in t.get("artists", [])])
                        result.append(f"• {t.get('name', 'N/A')} - {artists}")
                    return "\n".join(result) if result else "No tracks found."
                return f"Error: {resp.status_code} - {resp.text[:200]}"

            elif action == "get_playlists":
                resp = client.get(f"{base_url}/me/playlists", headers=headers, params={"limit": limit})
                if resp.status_code == 200:
                    playlists = resp.json().get("items", [])
                    result = []
                    for p in playlists:
                        result.append(f"• {p.get('name', 'N/A')} ({p.get('tracks', {}).get('total', 0)} tracks)")
                    return "\n".join(result) if result else "No playlists found."
                return f"Error: {resp.status_code} - {resp.text[:200]}"

            elif action == "play_playlist":
                if not playlist_id:
                    return "Error: playlist_id required for play_playlist"
                payload = {"context_uri": f"spotify:playlist:{playlist_id}"}
                resp = client.put(f"{base_url}/me/player/play", headers=headers, json=payload)
                if resp.status_code in [200, 204]:
                    return "Playing playlist! :white_check_mark:"
                return f"Error: {resp.status_code} - {resp.text[:200]}"

            else:
                return f"Error: Unknown action '{action}'. Available: play, pause, next, previous, search, get_playlists, currently_playing"

    except httpx.TimeoutException:
        return "Error: Request timed out after 30 seconds."
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    print("Spotify plugin loaded. Use 'spotify' tool in HelloChusquis.")