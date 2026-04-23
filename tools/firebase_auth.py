from httpx import AsyncClient
import json


async def verify_token(token: str) -> dict:
    """Verify Firebase ID token."""
    url = "https://identitytoolkit.googleapis.com/v1/accounts:lookup?key="
    async with AsyncClient() as client:
        r = await client.post(url, json={"idToken": token})
        return r.json()


async def get_user(email: str, api_key: str) -> dict:
    """Get Firebase user by email."""
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:query?key={api_key}"
    async with AsyncClient() as client:
        r = await client.post(url, json={"email": email})
        return r.json()


async def create_user(email: str, password: str, api_key: str) -> dict:
    """Create Firebase user."""
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}"
    async with AsyncClient() as client:
        r = await client.post(url, json={"email": email, "password": password, "returnSecureToken": True})
        return r.json()


async def delete_user(id_token: str, api_key: str) -> dict:
    """Delete Firebase user."""
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:delete?key={api_key}"
    async with AsyncClient() as client:
        r = await client.post(url, json={"idToken": id_token})
        return r.json()


async def reset_password(email: str, api_key: str) -> dict:
    """Send password reset email."""
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={api_key}"
    async with AsyncClient() as client:
        r = await client.post(url, json={"email": email, "requestType": "PASSWORD_RESET"})
        return r.json()