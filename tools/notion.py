"""Safe, bounded Notion API integration."""

from __future__ import annotations

import asyncio
import os
import re
from typing import Any, Optional

import httpx
from httpx import AsyncClient

_NOTION_API = "https://api.notion.com/v1"
_NOTION_VERSION = "2022-06-28"
_NOTION_TIMEOUT_SECONDS = 30
_NOTION_MAX_CHILDREN = 100
_NOTION_MAX_RICH_TEXT_CHARS = 2_000
_NOTION_MAX_TITLE_CHARS = 2_000
_NOTION_ID_RE = re.compile(r"^(?:[0-9a-fA-F]{32}|[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12})$")


def _client_kwargs() -> dict[str, Any]:
    return {"timeout": _NOTION_TIMEOUT_SECONDS, "follow_redirects": False}


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Notion-Version": _NOTION_VERSION}


def _notion_id(value: object, label: str) -> str:
    identifier = str(value or "")
    if not _NOTION_ID_RE.fullmatch(identifier):
        raise ValueError(f"Invalid Notion {label}.")
    return identifier


def _text_blocks(content: object) -> list[dict]:
    """Convert supplied text to Notion paragraph blocks without losing content."""
    if not isinstance(content, str):
        raise ValueError("Notion page content must be text.")
    blocks: list[dict] = []
    for line in content.splitlines():
        chunks = [line[index:index + _NOTION_MAX_RICH_TEXT_CHARS] for index in range(0, len(line), _NOTION_MAX_RICH_TEXT_CHARS)] or [""]
        for chunk in chunks:
            blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": chunk}}]},
                }
            )
    return blocks


def _children(content: object, children: Optional[list]) -> list:
    extra = [] if children is None else children
    if not isinstance(extra, list):
        raise ValueError("Notion children must be a list.")
    combined = _text_blocks(content) + extra
    if len(combined) > _NOTION_MAX_CHILDREN:
        raise ValueError(f"Notion requests support at most {_NOTION_MAX_CHILDREN} child blocks.")
    return combined


def _page_payload(parent_id: object, title: object, content: object, children: Optional[list]) -> dict:
    safe_parent_id = _notion_id(parent_id, "parent ID")
    safe_title = str(title or "")
    if not safe_title or len(safe_title) > _NOTION_MAX_TITLE_CHARS:
        raise ValueError("Notion page title is missing or too long.")
    return {
        "parent": {"page_id": safe_parent_id},
        "properties": {"title": {"title": [{"text": {"content": safe_title}}]}},
        "children": _children(content, children),
    }


def _properties(value: object) -> dict:
    if not isinstance(value, dict):
        raise ValueError("Notion properties must be an object.")
    return value


def _filter(value: object) -> dict:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("Notion database filter must be an object.")
    return {"filter": value}


def _response_text(response: httpx.Response) -> str:
    response.raise_for_status()
    return str(response.json())[:2000]


async def _async_request(method: str, path: str, token: str, **kwargs) -> dict:
    async with AsyncClient(**_client_kwargs()) as client:
        response = await client.request(method, f"{_NOTION_API}{path}", headers=_headers(token), **kwargs)
        response.raise_for_status()
        return response.json()


async def create_page(token: str, parent_id: str, title: str, content: str, children: Optional[list] = None) -> dict:
    """Create a Notion page and retain caller-provided text as child blocks."""
    return await _async_request("POST", "/pages", token, json=_page_payload(parent_id, title, content, children))


async def update_page(token: str, page_id: str, properties: dict) -> dict:
    """Update validated Notion page properties."""
    return await _async_request("PATCH", f"/pages/{_notion_id(page_id, 'page ID')}", token, json={"properties": _properties(properties)})


async def get_page(token: str, page_id: str) -> dict:
    """Retrieve a validated Notion page."""
    return await _async_request("GET", f"/pages/{_notion_id(page_id, 'page ID')}", token)


async def query_database(token: str, database_id: str, filter: dict | None = None) -> dict:
    """Query one bounded page of a validated Notion database."""
    payload = _filter(filter)
    payload["page_size"] = _NOTION_MAX_CHILDREN
    return await _async_request("POST", f"/databases/{_notion_id(database_id, 'database ID')}/query", token, json=payload)


async def append_block(token: str, block_id: str, children: list) -> dict:
    """Append a bounded list of blocks to a validated Notion block."""
    return await _async_request("PATCH", f"/blocks/{_notion_id(block_id, 'block ID')}/children", token, json={"children": _children("", children)})


def run(action: str, **kwargs) -> str:
    """Synchronous dispatcher for Notion API actions."""
    token = kwargs.get("token") or os.getenv("NOTION_TOKEN")
    if not token:
        return "Error: No Notion token found. Set NOTION_TOKEN environment variable."
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return _run_sync(action, str(token), kwargs)
        return loop.run_until_complete(_run_async(action, str(token), kwargs))
    except RuntimeError:
        return _run_sync(action, str(token), kwargs)
    except (httpx.HTTPError, ValueError) as exc:
        return f"Error: {exc}"


async def _run_async(action: str, token: str, kwargs: dict) -> str:
    if action == "create_page":
        result = await create_page(token, kwargs.get("parent_id", ""), kwargs.get("title", ""), kwargs.get("content", ""), kwargs.get("children"))
    elif action == "update_page":
        result = await update_page(token, kwargs.get("page_id", ""), kwargs.get("properties", {}))
    elif action == "get_page":
        result = await get_page(token, kwargs.get("page_id", ""))
    elif action == "query_database":
        result = await query_database(token, kwargs.get("database_id", ""), kwargs.get("filter"))
    elif action == "append_block":
        result = await append_block(token, kwargs.get("block_id", ""), kwargs.get("children", []))
    else:
        return "Error: Unknown action. Available: create_page, update_page, get_page, query_database, append_block"
    return str(result)[:2000]


def _run_sync(action: str, token: str, kwargs: dict) -> str:
    """Synchronous Notion dispatcher with a safe, closed HTTP client."""
    client = httpx.Client(**_client_kwargs())
    try:
        headers = _headers(token)
        if action == "create_page":
            response = client.post("https://api.notion.com/v1/pages", json=_page_payload(kwargs.get("parent_id", ""), kwargs.get("title", ""), kwargs.get("content", ""), kwargs.get("children")), headers=headers)
        elif action == "update_page":
            response = client.patch(f"{_NOTION_API}/pages/{_notion_id(kwargs.get('page_id'), 'page ID')}", json={"properties": _properties(kwargs.get("properties", {}))}, headers=headers)
        elif action == "get_page":
            response = client.get(f"{_NOTION_API}/pages/{_notion_id(kwargs.get('page_id'), 'page ID')}", headers=headers)
        elif action == "query_database":
            payload = _filter(kwargs.get("filter"))
            payload["page_size"] = _NOTION_MAX_CHILDREN
            response = client.post(f"{_NOTION_API}/databases/{_notion_id(kwargs.get('database_id'), 'database ID')}/query", json=payload, headers=headers)
        elif action == "append_block":
            response = client.patch(f"{_NOTION_API}/blocks/{_notion_id(kwargs.get('block_id'), 'block ID')}/children", json={"children": _children("", kwargs.get("children", []))}, headers=headers)
        else:
            return "Error: Unknown action. Available: create_page, update_page, get_page, query_database, append_block"
        return _response_text(response)
    except (httpx.HTTPError, ValueError) as exc:
        return f"Error: {exc}"
    finally:
        client.close()
