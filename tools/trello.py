"""Safe Trello API helpers using configured application credentials."""

from __future__ import annotations

import os

from httpx import AsyncClient

_BASE_URL = "https://api.trello.com/1"


def _auth_params(api_key: object, token: object) -> dict[str, str]:
    key = str(api_key or "")
    auth_token = str(token or "")
    if not key or key == "key" or not auth_token:
        raise ValueError("Trello requires a configured API key and token.")
    return {"key": key, "token": auth_token}


def _key(value: object | None) -> str:
    return str(value or os.getenv("TRELLO_API_KEY") or "")


async def _request(method: str, path: str, token: str, api_key: str | None = None, **kwargs) -> dict:
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.request(method, f"{_BASE_URL}{path}", params=_auth_params(_key(api_key), token), **kwargs)
        response.raise_for_status()
        return response.json()


async def create_board(name: str, token: str, api_key: str | None = None) -> dict:
    """Create a Trello board."""
    return await _request("POST", "/boards", token, api_key, json={"name": name})


async def get_board(board_id: str, token: str, api_key: str | None = None) -> dict:
    """Get a Trello board."""
    return await _request("GET", f"/boards/{board_id}", token, api_key)


async def create_list(board_id: str, name: str, token: str, api_key: str | None = None) -> dict:
    """Create a Trello list."""
    return await _request("POST", "/lists", token, api_key, json={"name": name, "idBoard": board_id})


async def create_card(list_id: str, name: str, desc: str, token: str, api_key: str | None = None) -> dict:
    """Create a Trello card."""
    return await _request("POST", "/cards", token, api_key, json={"name": name, "desc": desc, "idList": list_id})


async def add_member(card_id: str, member_id: str, token: str, api_key: str | None = None) -> dict:
    """Add a member to a Trello card."""
    return await _request("POST", f"/cards/{card_id}/members", token, api_key, json={"value": member_id})
