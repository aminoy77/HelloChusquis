"""Safe Monday.com GraphQL helpers using variables for all external values."""

from __future__ import annotations

from httpx import AsyncClient

_URL = "https://api.monday.com/v2"


def _create_board_payload(name: str) -> dict:
    return {
        "query": "mutation ($name: String!) { create_board(name: $name) { id } }",
        "variables": {"name": str(name)},
    }


async def _post(api_key: str, payload: dict) -> dict:
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.post(_URL, json=payload, headers={"Authorization": api_key})
        response.raise_for_status()
        return response.json()


async def create_board(name: str, api_key: str) -> dict:
    """Create a board using a parameterized mutation."""
    return await _post(api_key, _create_board_payload(name))


async def list_boards(api_key: str) -> dict:
    """List boards without external GraphQL interpolation."""
    return await _post(api_key, {"query": "{ boards { id name } }", "variables": {}})


async def create_item(api_key: str, board_id: str, name: str, **kwargs) -> dict:
    """Create an item using GraphQL variables."""
    payload = {
        "query": "mutation ($boardId: ID!, $name: String!) { create_item(board_id: $boardId, item_name: $name) { id } }",
        "variables": {"boardId": str(board_id), "name": str(name)},
    }
    return await _post(api_key, payload)


async def get_items(api_key: str, board_id: str) -> dict:
    """Get board items using a GraphQL variable."""
    payload = {
        "query": "query ($boardId: [ID!]) { boards(ids: $boardId) { items { id name } } }",
        "variables": {"boardId": [str(board_id)]},
    }
    return await _post(api_key, payload)


async def update_column(api_key: str, item_id: str, column_id: str, value: str) -> dict:
    """Update a column using GraphQL variables."""
    payload = {
        "query": "mutation ($itemId: ID!, $columnId: String!, $value: JSON!) { change_column_value(item_id: $itemId, column_id: $columnId, value: $value) { id } }",
        "variables": {"itemId": str(item_id), "columnId": str(column_id), "value": str(value)},
    }
    return await _post(api_key, payload)
