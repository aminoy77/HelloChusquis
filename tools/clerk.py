from httpx import AsyncClient


async def create_user(token: str, email: str, **kwargs) -> dict:
    """Create Clerk user."""
    url = "https://api.clerk.com/v1/users"
    async with AsyncClient() as client:
        r = await client.post(url, json={"email_address": [email], **kwargs}, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def get_user(token: str, user_id: str) -> dict:
    """Get Clerk user."""
    url = f"https://api.clerk.com/v1/users/{user_id}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def list_users(token: str, limit: int = 10) -> dict:
    """List Clerk users."""
    url = f"https://api.clerk.com/v1/users?limit={limit}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def update_user(token: str, user_id: str, **kwargs) -> dict:
    """Update Clerk user."""
    url = f"https://api.clerk.com/v1/users/{user_id}"
    async with AsyncClient() as client:
        r = await client.patch(url, json=kwargs, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def create_organization(token: str, name: str) -> dict:
    """Create Clerk organization."""
    url = "https://api.clerk.com/v1/organizations"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name}, headers={"Authorization": f"Bearer {token}"})
        return r.json()