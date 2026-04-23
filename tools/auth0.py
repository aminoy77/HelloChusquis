from httpx import AsyncClient


async def create_client(domain: str, token: str, name: str) -> dict:
    """Create Auth0 client."""
    url = f"https://{domain}/api/v2/clients"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name}, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def get_clients(domain: str, token: str) -> dict:
    """Get Auth0 clients."""
    url = f"https://{domain}/api/v2/clients"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def create_user(domain: str, token: str, email: str, password: str) -> dict:
    """Create Auth0 user."""
    url = f"https://{domain}/api/v2/users"
    async with AsyncClient() as client:
        r = await client.post(url, json={
            "email": email,
            "password": password,
            "connection": "Username-Password-Authentication"
        }, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def get_user(domain: str, token: str, user_id: str) -> dict:
    """Get Auth0 user."""
    url = f"https://{domain}/api/v2/users/{user_id}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def create_action(domain: str, token: str, name: str, code: str, trigger: str) -> dict:
    """Create Auth0 action."""
    url = f"https://{domain}/api/v2/actions/actions"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name, "code": code, "trigger": {"id": trigger}}, headers={"Authorization": f"Bearer {token}"})
        return r.json()