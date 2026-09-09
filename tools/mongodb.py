"""Safe, bounded MongoDB HTTP gateway integration."""

from __future__ import annotations

import asyncio
import json
import os
import re
from typing import Any, Optional
from urllib.parse import urlsplit

import httpx
from httpx import AsyncClient

from tools.web_fetch import SsrFBlockedError, validate_url_safety

_MONGODB_TIMEOUT_SECONDS = 30
_MONGODB_MAX_RESULTS = 100
_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


def _client_kwargs() -> dict[str, Any]:
    return {"timeout": _MONGODB_TIMEOUT_SECONDS, "follow_redirects": False}


def _api_base(value: object) -> str:
    """Accept only a public HTTPS REST gateway endpoint without credentials."""
    raw_url = str(value or "").strip().rstrip("/")
    parsed = urlsplit(raw_url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username is not None or parsed.password is not None:
        raise ValueError("MongoDB gateway URL must be public HTTPS without credentials.")
    try:
        return validate_url_safety(raw_url).rstrip("/")
    except (SsrFBlockedError, ValueError) as exc:
        raise ValueError("MongoDB gateway URL is unsafe.") from exc


def _identifier(value: object, label: str) -> str:
    candidate = str(value or "")
    if not _IDENTIFIER_RE.fullmatch(candidate):
        raise ValueError(f"Invalid MongoDB {label}.")
    return candidate


def _bounded_limit(value: object) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return 10
    return max(1, min(limit, _MONGODB_MAX_RESULTS))


def _document(value: object, label: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"MongoDB {label} must be an object.")
    if len(json.dumps(value, separators=(",", ":"))) > 65_536:
        raise ValueError(f"MongoDB {label} exceeds the allowed size.")
    return value


def _collection_url(mongo_uri: str, database: object, collection: object) -> str:
    return f"{_api_base(mongo_uri)}/{_identifier(database, 'database')}/{_identifier(collection, 'collection')}"


def _response_json(response: httpx.Response) -> dict:
    response.raise_for_status()
    return response.json()


async def list_databases(mongo_uri: str) -> dict:
    """List databases from a validated MongoDB REST gateway."""
    async with AsyncClient(**_client_kwargs()) as client:
        response = await client.get(f"{_api_base(mongo_uri)}/listDatabases")
        return _response_json(response)


async def list_collections(mongo_uri: str, database: str) -> dict:
    """List collections in a validated database."""
    async with AsyncClient(**_client_kwargs()) as client:
        response = await client.get(f"{_api_base(mongo_uri)}/{_identifier(database, 'database')}/listCollections")
        return _response_json(response)


async def insert_one(mongo_uri: str, database: str, collection: str, document: dict) -> dict:
    """Insert a bounded MongoDB document."""
    async with AsyncClient(**_client_kwargs()) as client:
        response = await client.post(_collection_url(mongo_uri, database, collection), json=_document(document, "document"))
        return _response_json(response)


async def find_documents(
    mongo_uri: str,
    database: str,
    collection: str,
    filter: Optional[dict] = None,
    limit: int = 10,
) -> dict:
    """Find a bounded number of documents through encoded query parameters."""
    criteria = _document({} if filter is None else filter, "filter")
    async with AsyncClient(**_client_kwargs()) as client:
        response = await client.get(
            _collection_url(mongo_uri, database, collection),
            params={"filter": json.dumps(criteria, separators=(",", ":")), "limit": _bounded_limit(limit)},
        )
        return _response_json(response)


async def delete_one(mongo_uri: str, database: str, collection: str, filter: dict) -> dict:
    """Delete one document selected by a validated filter."""
    async with AsyncClient(**_client_kwargs()) as client:
        response = await client.delete(_collection_url(mongo_uri, database, collection), json=_document(filter, "filter"))
        return _response_json(response)


def run(action: str, **kwargs) -> str:
    """Synchronous dispatcher for MongoDB REST gateway actions."""
    mongo_uri = kwargs.get("mongo_uri") or os.getenv("MONGO_URI")
    if not mongo_uri:
        return "Error: No MongoDB URI found. Set MONGO_URI environment variable."
    try:
        _api_base(mongo_uri)
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return _run_sync(action, str(mongo_uri), kwargs)
        return loop.run_until_complete(_run_async(action, str(mongo_uri), kwargs))
    except RuntimeError:
        return _run_sync(action, str(mongo_uri), kwargs)
    except (httpx.HTTPError, ValueError) as exc:
        return f"Error: {exc}"


async def _run_async(action: str, mongo_uri: str, kwargs: dict) -> str:
    """Async dispatcher for bounded MongoDB operations."""
    if action == "list_databases":
        result = await list_databases(mongo_uri)
    elif action == "list_collections":
        result = await list_collections(mongo_uri, kwargs.get("database", ""))
    elif action == "insert_one":
        result = await insert_one(mongo_uri, kwargs.get("database", ""), kwargs.get("collection", ""), kwargs.get("document", {}))
    elif action == "find_documents":
        result = await find_documents(mongo_uri, kwargs.get("database", ""), kwargs.get("collection", ""), kwargs.get("filter"), kwargs.get("limit", 10))
    elif action == "delete_one":
        result = await delete_one(mongo_uri, kwargs.get("database", ""), kwargs.get("collection", ""), kwargs.get("filter", {}))
    else:
        return "Error: Unknown action. Available: list_databases, list_collections, insert_one, find_documents, delete_one"
    return str(result)[:2000]


def _run_sync(action: str, mongo_uri: str, kwargs: dict) -> str:
    """Synchronous MongoDB dispatcher with a safe, closed HTTP client."""
    client = httpx.Client(**_client_kwargs())
    try:
        base_url = _api_base(mongo_uri)
        if action == "list_databases":
            response = client.get(f"{base_url}/listDatabases")
        elif action == "list_collections":
            response = client.get(f"{base_url}/{_identifier(kwargs.get('database'), 'database')}/listCollections")
        elif action == "insert_one":
            response = client.post(_collection_url(mongo_uri, kwargs.get("database"), kwargs.get("collection")), json=_document(kwargs.get("document", {}), "document"))
        elif action == "find_documents":
            response = client.get(
                _collection_url(mongo_uri, kwargs.get("database"), kwargs.get("collection")),
                params={"filter": json.dumps(_document(kwargs.get("filter", {}), "filter"), separators=(",", ":")), "limit": _bounded_limit(kwargs.get("limit", 10))},
            )
        elif action == "delete_one":
            response = client.delete(_collection_url(mongo_uri, kwargs.get("database"), kwargs.get("collection")), json=_document(kwargs.get("filter", {}), "filter"))
        else:
            return "Error: Unknown action. Available: list_databases, list_collections, insert_one, find_documents, delete_one"
        return str(_response_json(response))[:2000]
    except (httpx.HTTPError, ValueError) as exc:
        return f"Error: {exc}"
    finally:
        client.close()
