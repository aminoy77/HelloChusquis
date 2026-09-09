"""Safe Google Sheets API integration."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote

from httpx import AsyncClient


_SHEETS_BASE_URL = "https://sheets.googleapis.com/v4/spreadsheets"
_DRIVE_FILES_URL = "https://www.googleapis.com/drive/v3/files"
_SPREADSHEET_ID_RE = re.compile(r"[A-Za-z0-9_-]{1,256}")


def _spreadsheet_id(value: object) -> str:
    """Validate a spreadsheet identifier before embedding it in a path."""
    identifier = str(value or "").strip()
    if not _SPREADSHEET_ID_RE.fullmatch(identifier):
        raise ValueError("spreadsheet_id must be a single safe identifier.")
    return identifier


def _range_path(value: object) -> str:
    """Validate and encode an A1 range as one URL path segment."""
    range_value = str(value or "").strip()
    if not range_value or len(range_value) > 1024 or any(char in range_value for char in "\r\n\x00"):
        raise ValueError("range must be non-empty and cannot contain control characters.")
    return quote(range_value, safe="")


def _title(value: object, field_name: str) -> str:
    title = str(value or "").strip()
    if not title or len(title) > 100 or any(char in title for char in "\r\n\x00"):
        raise ValueError(f"{field_name} must be non-empty and cannot contain control characters.")
    return title


def _values(value: object) -> list[list[Any]]:
    if not isinstance(value, list) or not value or len(value) > 10000:
        raise ValueError("values must be a non-empty list containing at most 10,000 rows.")
    if any(not isinstance(row, list) or len(row) > 10000 for row in value):
        raise ValueError("values must be a list of rows with at most 10,000 cells each.")
    return value


def _bounded_page_size(value: object, default: int = 100) -> int:
    try:
        page_size = int(value)
    except (TypeError, ValueError):
        page_size = default
    return max(1, min(page_size, 1000))


def _headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"}


async def _request(
    method: str,
    url: str,
    api_key: str,
    *,
    json_data: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Perform one bounded Sheets request without following redirects."""
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.request(
            method,
            url,
            json=json_data,
            params=params,
            headers=_headers(api_key),
        )
        return response.json()


def _values_url(spreadsheet_id: object, range_: object) -> str:
    return f"{_SHEETS_BASE_URL}/{_spreadsheet_id(spreadsheet_id)}/values/{_range_path(range_)}"


async def create_sheet(title: str, sheet_title: str, api_key: str) -> dict[str, Any]:
    """Create a spreadsheet with validated document and initial sheet titles."""
    return await _request(
        "POST",
        _SHEETS_BASE_URL,
        api_key,
        json_data={
            "properties": {"title": _title(title, "title")},
            "sheets": [{"properties": {"title": _title(sheet_title, "sheet_title")}}],
        },
    )


async def get_sheet(spreadsheet_id: str, range_: str, api_key: str) -> dict[str, Any]:
    """Read values from a validated spreadsheet and encoded A1 range."""
    return await _request("GET", _values_url(spreadsheet_id, range_), api_key)


async def update_sheet(spreadsheet_id: str, range_: str, values: list[list[Any]], api_key: str) -> dict[str, Any]:
    """Write raw values to a validated range without evaluating spreadsheet formulas."""
    return await _request(
        "PUT",
        _values_url(spreadsheet_id, range_),
        api_key,
        json_data={"values": _values(values)},
        params={"valueInputOption": "RAW"},
    )


async def append_row(spreadsheet_id: str, range_: str, values: list[list[Any]], api_key: str) -> dict[str, Any]:
    """Append raw values to a validated range without evaluating formulas."""
    return await _request(
        "POST",
        f"{_values_url(spreadsheet_id, range_)}:append",
        api_key,
        json_data={"values": _values(values)},
        params={"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"},
    )


async def list_sheets(api_key: str, page_size: int = 100) -> dict[str, Any]:
    """List a bounded page of spreadsheet files from Drive."""
    return await _request(
        "GET",
        _DRIVE_FILES_URL,
        api_key,
        params={
            "q": "mimeType='application/vnd.google-apps.spreadsheet' and trashed = false",
            "pageSize": _bounded_page_size(page_size),
        },
    )
