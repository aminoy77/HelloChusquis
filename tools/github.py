from httpx import AsyncClient


async def create_repo(name: str, description: str, private: bool, token: str) -> dict:
    """Create GitHub repository."""
    url = "https://api.github.com/user/repos"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name, "description": description, "private": private}, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def get_repo(owner: str, repo: str, token: str) -> dict:
    """Get GitHub repository."""
    url = f"https://api.github.com/repos/{owner}/{repo}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def create_issue(owner: str, repo: str, title: str, body: str, token: str) -> dict:
    """Create GitHub issue."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    async with AsyncClient() as client:
        r = await client.post(url, json={"title": title, "body": body}, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def list_issues(owner: str, repo: str, state: str, token: str) -> dict:
    """List GitHub issues."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues?state={state}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def create_release(owner: str, repo: str, tag: str, name: str, body: str, token: str) -> dict:
    """Create GitHub release."""
    url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    async with AsyncClient() as client:
        r = await client.post(url, json={"tag_name": tag, "name": name, "body": body}, headers={"Authorization": f"Bearer {token}"})
        return r.json()