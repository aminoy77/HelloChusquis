from httpx import AsyncClient
import os
import httpx


def run(action: str, **kwargs) -> str:
    """Synchronous dispatcher for Clerk API actions."""
    token = kwargs.get("token") or os.getenv("CLERK_SECRET_KEY")
    if not token:
        return "Error: No Clerk token found. Set CLERK_SECRET_KEY environment variable."

    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return _run_sync(action, token, kwargs)
        return loop.run_until_complete(_run_async(action, token, kwargs))
    except RuntimeError:
        return _run_sync(action, token, kwargs)


async def _run_async(action: str, token: str, kwargs: dict) -> str:
    """Async dispatcher for Clerk operations."""
    if action == "create_user":
        return await create_user(token, kwargs.get("email", ""), **{k: v for k, v in kwargs.items() if k not in ("token", "email")})
    elif action == "get_user":
        return await get_user(token, kwargs.get("user_id", ""))
    elif action == "list_users":
        return await list_users(token, kwargs.get("limit", 10))
    elif action == "update_user":
        return await update_user(token, kwargs.get("user_id", ""), **{k: v for k, v in kwargs.items() if k not in ("token", "user_id")})
    elif action == "create_organization":
        return await create_organization(token, kwargs.get("name", ""))
    else:
        return f"Error: Unknown action '{action}'. Available: create_user, get_user, list_users, update_user, create_organization"


def _run_sync(action: str, token: str, kwargs: dict) -> str:
    """Synchronous fallback using httpx.Client."""
    base_url = "https://api.clerk.com/v1"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        client = httpx.Client(timeout=30)
        if action == "create_user":
            r = client.post(f"{base_url}/users", json={"email_address": [kwargs.get("email", "")]}, headers=headers)
            return str(r.json())[:2000]
        elif action == "get_user":
            r = client.get(f"{base_url}/users/{kwargs.get('user_id', '')}", headers=headers)
            return str(r.json())[:2000]
        elif action == "list_users":
            r = client.get(f"{base_url}/users?limit={kwargs.get('limit', 10)}", headers=headers)
            return str(r.json())[:2000]
        elif action == "update_user":
            user_id = kwargs.get("user_id", "")
            update_data = {k: v for k, v in kwargs.items() if k not in ("token", "user_id")}
            r = client.patch(f"{base_url}/users/{user_id}", json=update_data, headers=headers)
            return str(r.json())[:2000]
        elif action == "create_organization":
            r = client.post(f"{base_url}/organizations", json={"name": kwargs.get("name", "")}, headers=headers)
            return str(r.json())[:2000]
        else:
            return f"Error: Unknown action '{action}'. Available: create_user, get_user, list_users, update_user, create_organization"
    except Exception as e:
        return f"Error: {str(e)}"


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