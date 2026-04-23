from httpx import AsyncClient


async def list_databases(mongo_uri: str) -> dict:
    """List MongoDB databases."""
    url = mongo_uri + "/listDatabases"
    async with AsyncClient() as client:
        r = await client.get(url)
        return r.json()


async def list_collections(mongo_uri: str, database: str) -> dict:
    """List collections in MongoDB."""
    url = f"{mongo_uri}/{database}/listCollections"
    async with AsyncClient() as client:
        r = await client.get(url)
        return r.json()


async def insert_one(mongo_uri: str, database: str, collection: str, document: dict) -> dict:
    """Insert document to MongoDB."""
    url = f"{mongo_uri}/{database}/{collection}"
    async with AsyncClient() as client:
        r = await client.post(url, json=document)
        return r.json()


async def find_documents(mongo_uri: str, database: str, collection: str, filter: dict = {}, limit: int = 10) -> dict:
    """Find documents in MongoDB."""
    url = f"{mongo_uri}/{database}/{collection}?filter={filter}&limit={limit}"
    async with AsyncClient() as client:
        r = await client.get(url)
        return r.json()


async def delete_one(mongo_uri: str, database: str, collection: str,filter: dict) -> dict:
    """Delete document from MongoDB."""
    url = f"{mongo_uri}/{database}/{collection}"
    async with AsyncClient() as client:
        r = await client.delete(url, json=filter)
        return r.json()