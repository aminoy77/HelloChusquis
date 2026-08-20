"""Safe, bounded Supabase API integration."""

from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx
from httpx import AsyncClient

_SUPABASE_MANAGEMENT_API = "https://api.supabase.com/v1"
_SUPABASE_TIMEOUT_SECONDS = 30
_SUPABASE_MAX_ROWS = 100
_SUPABASE_MAX_PAYLOAD_BYTES = 65_536
_PROJECT_REF_RE = re.compile(r"^[a-z0-9]{20,64}$")
_TABLE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")


def _client_kwargs() -> dict[str, Any]:
    return {"timeout": _SUPABASE_TIMEOUT_SECONDS, "follow_redirects": False}


def _project_ref(value: object) -> str:
    reference = str(value or "")
    if not _PROJECT_REF_RE.fullmatch(reference):
        raise ValueError("Invalid Supabase project reference.")
    return reference


def _table(value: object) -> str:
    table_name = str(value or "")
    if not _TABLE_RE.fullmatch(table_name):
        raise ValueError("Invalid Supabase table name.")
    return table_name


def _data(value: object) -> dict:
    if not isinstance(value, dict):
        raise ValueError("Supabase row data must be an object.")
    if len(json.dumps(value, separators=(",", ":"))) > _SUPABASE_MAX_PAYLOAD_BYTES:
        raise ValueError("Supabase row data exceeds the allowed size.")
    return value


def _sql(value: object) -> str:
    query = str(value or "")
    if not query.strip() or len(query) > _SUPABASE_MAX_PAYLOAD_BYTES or "\x00" in query:
        raise ValueError("Invalid Supabase SQL query.")
    return query


def _management_headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"}


def _rest_headers(api_key: str) -> dict[str, str]:
    return {"apikey": api_key, "Authorization": f"Bearer {api_key}", "Range": f"0-{_SUPABASE_MAX_ROWS - 1}"}


def _rest_url(ref: object, path: str) -> str:
    return f"https://{_project_ref(ref)}.supabase.co/rest/v1/{path}"


def _response_json(response: httpx.Response) -> dict:
    response.raise_for_status()
    return response.json()


def run(action: str, **kwargs) -> str:
    """Synchronous dispatcher for approved Supabase operations."""
    api_key = kwargs.get("api_key") or os.getenv("SUPABASE_API_KEY")
    if not api_key:
        return "Error: No Supabase API key found. Set SUPABASE_API_KEY environment variable."
    # A synchronous external call cannot safely wait on the current running loop.
    return _run_sync(action, str(api_key), kwargs)


async def _run_async(action: str, api_key: str, kwargs: dict) -> str:
    if action == "create_project":
        result = await create_project(kwargs.get("name", ""), kwargs.get("slug", ""), api_key)
    elif action == "get_project":
        result = await get_project(kwargs.get("ref", ""), api_key)
    elif action == "query_table":
        result = await query_table(kwargs.get("ref", ""), kwargs.get("table", ""), api_key)
    elif action == "insert_row":
        result = await insert_row(kwargs.get("ref", ""), kwargs.get("table", ""), kwargs.get("data", {}), api_key)
    elif action == "run_sql":
        result = await run_sql(kwargs.get("ref", ""), kwargs.get("sql", ""), api_key)
    else:
        return "Error: Unknown action. Available: create_project, get_project, query_table, insert_row, run_sql"
    return str(result)[:2000]


def _run_sync(action: str, api_key: str, kwargs: dict) -> str:
    """Synchronous fallback using a safe, closed HTTP client."""
    client = httpx.Client(**_client_kwargs())
    try:
        if action == "create_project":
            response = client.post(
                f"{_SUPABASE_MANAGEMENT_API}/projects",
                json={"name": str(kwargs.get("name", ""))[:100], "slug": str(kwargs.get("slug", ""))[:100]},
                headers=_management_headers(api_key),
            )
        elif action == "get_project":
            response = client.get(f"{_SUPABASE_MANAGEMENT_API}/projects/{_project_ref(kwargs.get('ref'))}", headers=_management_headers(api_key))
        elif action == "query_table":
            response = client.get(_rest_url(kwargs.get("ref"), _table(kwargs.get("table"))), headers=_rest_headers(api_key))
        elif action == "insert_row":
            response = client.post(_rest_url(kwargs.get("ref"), _table(kwargs.get("table"))), json=_data(kwargs.get("data", {})), headers=_rest_headers(api_key))
        elif action == "run_sql":
            response = client.post(_rest_url(kwargs.get("ref"), "rpc/exec_sql"), json={"query": _sql(kwargs.get("sql", ""))}, headers=_rest_headers(api_key))
        else:
            return "Error: Unknown action. Available: create_project, get_project, query_table, insert_row, run_sql"
        return str(_response_json(response))[:2000]
    except (httpx.HTTPError, ValueError) as exc:
        return f"Error: {exc}"
    finally:
        client.close()


async def create_project(name: str, slug: str, api_key: str) -> dict:
    """Create a Supabase project with bounded metadata."""
    async with AsyncClient(**_client_kwargs()) as client:
        response = await client.post(f"{_SUPABASE_MANAGEMENT_API}/projects", json={"name": str(name)[:100], "slug": str(slug)[:100]}, headers=_management_headers(api_key))
        return _response_json(response)


async def get_project(ref: str, api_key: str) -> dict:
    """Get a validated Supabase project."""
    async with AsyncClient(**_client_kwargs()) as client:
        response = await client.get(f"{_SUPABASE_MANAGEMENT_API}/projects/{_project_ref(ref)}", headers=_management_headers(api_key))
        return _response_json(response)


async def query_table(ref: str, table: str, api_key: str) -> dict:
    """Read a bounded Supabase table range."""
    async with AsyncClient(**_client_kwargs()) as client:
        response = await client.get(_rest_url(ref, _table(table)), headers=_rest_headers(api_key))
        return _response_json(response)


async def insert_row(ref: str, table: str, data: dict, api_key: str) -> dict:
    """Insert one validated Supabase row."""
    async with AsyncClient(**_client_kwargs()) as client:
        response = await client.post(_rest_url(ref, _table(table)), json=_data(data), headers=_rest_headers(api_key))
        return _response_json(response)


async def run_sql(ref: str, sql: str, api_key: str) -> dict:
    """Execute validated SQL only after the central approval gate permits it."""
    async with AsyncClient(**_client_kwargs()) as client:
        response = await client.post(_rest_url(ref, "rpc/exec_sql"), json={"query": _sql(sql)}, headers=_rest_headers(api_key))
        return _response_json(response)
