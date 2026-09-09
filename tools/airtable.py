"""Safe Airtable integration aligned with the agent's public action schema."""

from __future__ import annotations

import json
import os
import re
from urllib.parse import quote

import httpx

from tools.base import ToolResult

PLUGIN_NAME = "airtable"
PLUGIN_DESCRIPTION = "Airtable - collaborative bases"
MAX_AIRTABLE_RECORDS = 100
MAX_AIRTABLE_PAYLOAD_BYTES = 65_536
_BASE_ID_RE = re.compile(r"^app[A-Za-z0-9]{14}$")
_RECORD_ID_RE = re.compile(r"^rec[A-Za-z0-9]{14}$")


def _base_id(value: object) -> str:
    base_id = str(value or "")
    if not _BASE_ID_RE.fullmatch(base_id):
        raise ValueError("Invalid Airtable base ID.")
    return base_id


def _table(value: object) -> str:
    table = str(value or "Table1")
    if not table or len(table) > 100 or "\x00" in table or "\r" in table or "\n" in table:
        raise ValueError("Invalid Airtable table name.")
    return quote(table, safe="")


def _record_id(value: object) -> str:
    record_id = str(value or "")
    if not _RECORD_ID_RE.fullmatch(record_id):
        raise ValueError("Invalid Airtable record ID.")
    return record_id


def _fields(value: object) -> dict:
    if not isinstance(value, dict):
        raise ValueError("Airtable fields must be an object.")
    if len(json.dumps(value, separators=(",", ":"))) > MAX_AIRTABLE_PAYLOAD_BYTES:
        raise ValueError("Airtable fields exceed the allowed size.")
    return value


def _url(base_id: object, table: object, record_id: object | None = None) -> str:
    url = f"https://api.airtable.com/v0/{_base_id(base_id)}/{_table(table)}"
    return f"{url}/{_record_id(record_id)}" if record_id is not None else url


def _result(response: httpx.Response) -> ToolResult:
    try:
        payload = str(response.json())[:2000]
    except ValueError:
        payload = response.text[:500]
    return ToolResult(response.status_code in {200, 201}, payload, "" if response.status_code in {200, 201} else payload)


def run(action: str = "list_records", **kwargs) -> ToolResult:
    """Execute bounded Airtable operations using the actions exposed by the agent."""
    token = kwargs.get("token") or os.getenv("AIRTABLE_API_TOKEN")
    if not token:
        return ToolResult(False, "", "Airtable token required. Set AIRTABLE_API_TOKEN environment variable.")

    base_id = kwargs.get("base_id") or os.getenv("AIRTABLE_BASE_ID")
    if not base_id:
        return ToolResult(False, "", "Airtable base_id required (pass base_id or set AIRTABLE_BASE_ID)")

    headers = {"Authorization": f"Bearer {token}"}
    try:
        if action in {"list", "list_records"}:
            response = httpx.get(
                _url(base_id, kwargs.get("table", "Table1")),
                headers=headers,
                params={"pageSize": MAX_AIRTABLE_RECORDS},
                timeout=30,
                follow_redirects=False,
            )
            return _result(response)

        fields = _fields(kwargs.get("fields", kwargs.get("data", {})))
        if action in {"create", "create_record"}:
            response = httpx.post(
                _url(base_id, kwargs.get("table", "Table1")),
                headers=headers,
                json={"fields": fields},
                timeout=30,
                follow_redirects=False,
            )
            return _result(response)

        if action == "update_record":
            response = httpx.patch(
                _url(base_id, kwargs.get("table", "Table1"), kwargs.get("id")),
                headers=headers,
                json={"fields": fields},
                timeout=30,
                follow_redirects=False,
            )
            return _result(response)

        if action == "delete_record":
            response = httpx.delete(
                _url(base_id, kwargs.get("table", "Table1"), kwargs.get("id")),
                headers=headers,
                timeout=30,
                follow_redirects=False,
            )
            return _result(response)

        return ToolResult(False, "", "Unknown action. Available: list_records, create_record, update_record, delete_record")
    except (httpx.HTTPError, ValueError) as exc:
        return ToolResult(False, "", str(exc))
