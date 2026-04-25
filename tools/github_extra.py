from httpx import AsyncClient
import json


async def search_github(query: str, token: str = None, sort: str = "best-match") -> dict:
    """Search GitHub repos."""
    url = f"https://api.github.com/search/repositories?q={query}&sort={sort}"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with AsyncClient() as client:
        r = await client.get(url, headers=headers)
        return r.json()


async def get_github_user(username: str, token: str = None) -> dict:
    """Get GitHub user info."""
    url = f"https://api.github.com/users/{username}"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with AsyncClient() as client:
        r = await client.get(url, headers=headers)
        return r.json()


async def list_github_gists(username: str, token: str = None) -> dict:
    """List GitHub gists."""
    url = f"https://api.github.com/users/{username}/gists"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with AsyncClient() as client:
        r = await client.get(url, headers=headers)
        return r.json()


async def get_github_rate_limit(token: str) -> dict:
    """Get GitHub rate limit."""
    url = "https://api.github.com/rate_limit"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def create_github_gist(token: str, description: str, files: dict, public: bool = False) -> dict:
    """Create GitHub gist."""
    url = "https://api.github.com/gists"
    async with AsyncClient() as client:
        r = await client.post(url, json={"description": description, "public": public, "files": files}, 
            headers={"Authorization": f"Bearer {token}"})
        return r.json()