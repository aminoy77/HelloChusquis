from httpx import AsyncClient


async def create_board(name: str, token: str) -> dict:
    """Create Trello board."""
    url = "https://api.trello.com/1/boards"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name, "key": "key", "token": token})
        return r.json()


async def get_board(board_id: str, token: str) -> dict:
    """Get Trello board."""
    url = f"https://api.trello.com/1/boards/{board_id}"
    async with AsyncClient() as client:
        r = await client.get(url, params={"key": "key", "token": token})
        return r.json()


async def create_list(board_id: str, name: str, token: str) -> dict:
    """Create Trello list."""
    url = "https://api.trello.com/1/lists"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name, "idBoard": board_id, "key": "key", "token": token})
        return r.json()


async def create_card(list_id: str, name: str, desc: str, token: str) -> dict:
    """Create Trello card."""
    url = "https://api.trello.com/1/cards"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name, "desc": desc, "idList": list_id, "key": "key", "token": token})
        return r.json()


async def add_member(card_id: str, member_id: str, token: str) -> dict:
    """Add member to Trello card."""
    url = f"https://api.trello.com/1/cards/{card_id}/members"
    async with AsyncClient() as client:
        r = await client.post(url, json={"value": member_id, "key": "key", "token": token})
        return r.json()