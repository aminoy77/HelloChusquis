from httpx import AsyncClient


async def get(url: str, headers: dict = None) -> dict:
    """Generic GET request."""
    async with AsyncClient() as client:
        r = await client.get(url, headers=headers or {})
        try:
            return r.json()
        except:
            return {"text": r.text}


async def post(url: str, json: dict = None, data: dict = None, headers: dict = None) -> dict:
    """Generic POST request."""
    async with AsyncClient() as client:
        r = await client.post(url, json=json, data=data, headers=headers or {})
        try:
            return r.json()
        except:
            return {"text": r.text}


async def put(url: str, json: dict = None, headers: dict = None) -> dict:
    """Generic PUT request."""
    async with AsyncClient() as client:
        r = await client.put(url, json=json, headers=headers or {})
        try:
            return r.json()
        except:
            return {"text": r.text}


async def delete(url: str, headers: dict = None) -> dict:
    """Generic DELETE request."""
    async with AsyncClient() as client:
        r = await client.delete(url, headers=headers or {})
        return {"status": r.status_code}


async def patch(url: str, json: dict = None, headers: dict = None) -> dict:
    """Generic PATCH request."""
    async with AsyncClient() as client:
        r = await client.patch(url, json=json, headers=headers or {})
        try:
            return r.json()
        except:
            return {"text": r.text}