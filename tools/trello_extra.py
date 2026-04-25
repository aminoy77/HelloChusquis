from httpx import AsyncClient


async def create_project(name: str, description: str, color: str, token: str) -> dict:
    """Create Trello project."""
    url = "https://api.trello.com/1/boards"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name, "desc": description, "prefs_background": color},
            params={"key": "key", "token": token})
        return r.json()


async def get_board(board_id: str, key: str, token: str) -> dict:
    """Get Trello board."""
    url = f"https://api.trello.com/1/boards/{board_id}"
    async with AsyncClient() as client:
        r = await client.get(url, params={"key": key, "token": token})
        return r.json()


async def add_card(list_id: str, name: str, desc: str, key: str, token: str) -> dict:
    """Add card to Trello list."""
    url = "https://api.trello.com/1/cards"
    async with AsyncClient() as client:
        r = await client.post(url, json={"idList": list_id, "name": name, "desc": desc},
            params={"key": key, "token": token})
        return r.json()


async def add_comment(card_id: str, text: str, key: str, token: str) -> dict:
    """Add comment to Trello card."""
    url = f"https://api.trello.com/1/cards/{card_id}/actions/comments"
    async with AsyncClient() as client:
        r = await client.post(url, json={"text": text}, params={"key": key, "token": token})
        return r.json()


async def move_card(card_id: str, list_id: str, key: str, token: str) -> dict:
    """Move Trello card to another list."""
    url = f"https://api.trello.com/1/cards/{card_id}"
    async with AsyncClient() as client:
        r = await client.put(url, json={"idList": list_id}, params={"key": key, "token": token})
        return r.json()


async def create_checklist(card_id: str, name: str, key: str, token: str) -> dict:
    """Create Trello checklist."""
    url = f"https://api.trello.com/1/cards/{card_id}/checklists"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name}, params={"key": key, "token": token})
        return r.json()


async def add_label(board_id: str, name: str, color: str, key: str, token: str) -> dict:
    """Add label to Trello board."""
    url = f"https://api.trello.com/1/boards/{board_id}/labels"
    async with AsyncClient() as client:
        r = await client.post(url, json={"name": name, "color": color}, params={"key": key, "token": token})
        return r.json()