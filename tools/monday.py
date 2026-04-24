from httpx import AsyncClient


async def create_board(name: str, api_key: str) -> dict:
    """Create Monday.com board."""
    url = "https://api.monday.com/v2"
    async with AsyncClient() as client:
        r = await client.post(url, json={"query": f'mutation {{ create_board(name: "{name}") {{ id }} }}', "variables": {}}, headers={"Authorization": api_key})
        return r.json()


async def list_boards(api_key: str) -> dict:
    """List Monday.com boards."""
    url = "https://api.monday.com/v2"
    async with AsyncClient() as client:
        r = await client.post(url, json={"query": "{ boards { id name } }"}, headers={"Authorization": api_key})
        return r.json()


async def create_item(api_key: str, board_id: str, name: str, **kwargs) -> dict:
    """Create Monday.com item."""
    url = "https://api.monday.com/v2"
    query = f'mutation {{ create_item(board_id: "{board_id}", item_name: "{name}") {{ id }} }}'
    async with AsyncClient() as client:
        r = await client.post(url, json={"query": query}, headers={"Authorization": api_key})
        return r.json()


async def get_items(api_key: str, board_id: str) -> dict:
    """Get Monday.com items."""
    url = "https://api.monday.com/v2"
    async with AsyncClient() as client:
        r = await client.post(url, json={"query": f'{{ boards(ids: "{board_id}") {{ items {{ id name }} }} }}'}, headers={"Authorization": api_key})
        return r.json()


async def update_column(api_key: str, item_id: str, column_id: str, value: str) -> dict:
    """Update Monday.com column."""
    url = "https://api.monday.com/v2"
    query = f'mutation {{ change_column_value(item_id: "{item_id}", column_id: "{column_id}", value: "{value}") {{ id }} }}'
    async with AsyncClient() as client:
        r = await client.post(url, json={"query": query}, headers={"Authorization": api_key})
        return r.json()