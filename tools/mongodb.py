from typing import Optional
from httpx import AsyncClient
import os
import httpx


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


async def find_documents(mongo_uri: str, database: str, collection: str, filter: Optional[dict] = None, limit: int = 10) -> dict:
    """Find documents in MongoDB."""
    if filter is None:
        filter = {}
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


def run(action: str, **kwargs) -> str:
    """Synchronous dispatcher for MongoDB API actions."""
    mongo_uri = kwargs.get("mongo_uri") or os.getenv("MONGO_URI")
    if not mongo_uri:
        return "Error: No MongoDB URI found. Set MONGO_URI environment variable."
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return _run_sync(action, mongo_uri, kwargs)
        return loop.run_until_complete(_run_async(action, mongo_uri, kwargs))
    except RuntimeError:
        return _run_sync(action, mongo_uri, kwargs)


async def _run_async(action: str, mongo_uri: str, kwargs: dict) -> str:
    """Async dispatcher for MongoDB operations."""
    if action == "list_databases":
        return str(await list_databases(mongo_uri))
    elif action == "list_collections":
        return str(await list_collections(mongo_uri, kwargs.get("database", "")))
    elif action == "insert_one":
        return str(await insert_one(mongo_uri, kwargs.get("database", ""), kwargs.get("collection", ""), kwargs.get("document", {})))
    elif action == "find_documents":
        return str(await find_documents(mongo_uri, kwargs.get("database", ""), kwargs.get("collection", ""), kwargs.get("filter"), kwargs.get("limit", 10)))
    elif action == "delete_one":
        return str(await delete_one(mongo_uri, kwargs.get("database", ""), kwargs.get("collection", ""), kwargs.get("filter", {})))
    else:
        return f"Error: Unknown action '{action}'. Available: list_databases, list_collections, insert_one, find_documents, delete_one"


def _run_sync(action: str, mongo_uri: str, kwargs: dict) -> str:
    """Synchronous fallback using httpx.Client."""
    try:
        client = httpx.Client(timeout=30)
        if action == "list_databases":
            r = client.get(f"{mongo_uri}/listDatabases")
            return str(r.json())[:2000]
        elif action == "list_collections":
            r = client.get(f"{mongo_uri}/{kwargs.get('database', '')}/listCollections")
            return str(r.json())[:2000]
        elif action == "insert_one":
            r = client.post(f"{mongo_uri}/{kwargs.get('database', '')}/{kwargs.get('collection', '')}",
                           json=kwargs.get("document", {}))
            return str(r.json())[:2000]
        elif action == "find_documents":
            f = kwargs.get("filter", {})
            limit = kwargs.get("limit", 10)
            r = client.get(f"{mongo_uri}/{kwargs.get('database', '')}/{kwargs.get('collection', '')}",
                          params={"filter": f, "limit": limit})
            return str(r.json())[:2000]
        elif action == "delete_one":
            r = client.delete(f"{mongo_uri}/{kwargs.get('database', '')}/{kwargs.get('collection', '')}",
                             json=kwargs.get("filter", {}))
            return str(r.json())[:2000]
        else:
            return f"Error: Unknown action '{action}'. Available: list_databases, list_collections, insert_one, find_documents, delete_one"
    except Exception as e:
        return f"Error: {str(e)}"