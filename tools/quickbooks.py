"""Safe asynchronous QuickBooks Online API helpers."""

from __future__ import annotations

import os
import re
from typing import Any

import httpx
from httpx import AsyncClient


QUICKBOOKS_API_BASE = "https://quickbooks.api.intuit.com/v3/company"
QUICKBOOKS_TIMEOUT_SECONDS = 30
QUICKBOOKS_MAX_RESULTS_DEFAULT = 10
QUICKBOOKS_MAX_RESULTS_MAX = 100
_COMPANY_ID_RE = re.compile(r"^\d{1,20}$")
_ENTITY_ID_RE = re.compile(r"^\d{1,20}$")


def _company_url(resource: str, company_id: str | None = None) -> str:
    """Build a validated company-scoped QuickBooks endpoint URL."""
    resolved_company_id = company_id or os.getenv("QUICKBOOKS_COMPANY_ID", "")
    if not _COMPANY_ID_RE.fullmatch(resolved_company_id):
        raise ValueError("QUICKBOOKS_COMPANY_ID must be a numeric company identifier")
    return f"{QUICKBOOKS_API_BASE}/{resolved_company_id}/{resource.lstrip('/')}"


def _authorization_header(access_token: str) -> dict[str, str]:
    if not isinstance(access_token, str) or not access_token.strip():
        raise ValueError("QuickBooks access token is required")
    return {"Authorization": f"Bearer {access_token}"}


def _bounded_max_results(value: Any) -> int:
    try:
        requested = int(value)
    except (TypeError, ValueError):
        return QUICKBOOKS_MAX_RESULTS_DEFAULT
    return max(1, min(requested, QUICKBOOKS_MAX_RESULTS_MAX))


async def _request(method: str, url: str, access_token: str, **kwargs: Any) -> dict:
    """Perform a bounded QuickBooks request and return an error object on transport failure."""
    try:
        async with AsyncClient(
            timeout=QUICKBOOKS_TIMEOUT_SECONDS,
            follow_redirects=False,
        ) as client:
            response = await getattr(client, method)(
                url,
                headers=_authorization_header(access_token),
                **kwargs,
            )
            response.raise_for_status()
            return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        return {"error": f"QuickBooks request failed: {exc}"}


async def create_invoice(
    customer_id: str,
    line_items: list[dict[str, Any]],
    access_token: str,
    company_id: str | None = None,
) -> dict:
    """Create a QuickBooks invoice for a validated company context."""
    if not _ENTITY_ID_RE.fullmatch(str(customer_id)):
        return {"error": "customer_id must be numeric"}
    if not isinstance(line_items, list) or not line_items:
        return {"error": "line_items must be a non-empty list"}
    try:
        url = _company_url("invoice", company_id)
    except ValueError as exc:
        return {"error": str(exc)}
    return await _request(
        "post",
        url,
        access_token,
        json={"CustomerRef": {"value": customer_id}, "Line": line_items},
    )


async def get_invoice(
    invoice_id: str,
    access_token: str,
    company_id: str | None = None,
) -> dict:
    """Fetch one numeric QuickBooks invoice identifier."""
    if not _ENTITY_ID_RE.fullmatch(str(invoice_id)):
        return {"error": "invoice_id must be numeric"}
    try:
        url = _company_url(f"invoice/{invoice_id}", company_id)
    except ValueError as exc:
        return {"error": str(exc)}
    return await _request("get", url, access_token)


async def create_customer(
    name: str,
    email: str,
    access_token: str,
    company_id: str | None = None,
) -> dict:
    """Create a customer in a validated QuickBooks company context."""
    if not isinstance(name, str) or not name.strip() or len(name) > 100:
        return {"error": "customer name must contain 1-100 characters"}
    if not isinstance(email, str) or len(email) > 254 or "@" not in email:
        return {"error": "customer email is invalid"}
    try:
        url = _company_url("customer", company_id)
    except ValueError as exc:
        return {"error": str(exc)}
    return await _request(
        "post",
        url,
        access_token,
        json={"DisplayName": name, "PrimaryEmailAddr": {"Address": email}},
    )


async def get_customers(
    access_token: str,
    max_results: int = QUICKBOOKS_MAX_RESULTS_DEFAULT,
    company_id: str | None = None,
) -> dict:
    """List a bounded number of customers through a static QuickBooks query."""
    try:
        url = _company_url("query", company_id)
    except ValueError as exc:
        return {"error": str(exc)}
    query = f"SELECT Id, DisplayName FROM Customer MAXRESULTS {_bounded_max_results(max_results)}"
    return await _request("get", url, access_token, params={"query": query})


async def create_vendor(
    name: str,
    access_token: str,
    company_id: str | None = None,
) -> dict:
    """Create a vendor in a validated QuickBooks company context."""
    if not isinstance(name, str) or not name.strip() or len(name) > 100:
        return {"error": "vendor name must contain 1-100 characters"}
    try:
        url = _company_url("vendor", company_id)
    except ValueError as exc:
        return {"error": str(exc)}
    return await _request("post", url, access_token, json={"DisplayName": name})
