"""Safe GitHub Actions integration."""

from __future__ import annotations

import re
from typing import Any

import httpx


_BASE_URL = "https://api.github.com"
_SEGMENT_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}")
_WORKFLOW_RE = re.compile(r"(?:[1-9][0-9]{0,18}|[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\.(?:ya?ml))")


def _repository(value: object) -> str:
    """Validate an owner/repository pair before embedding it in a GitHub API path."""
    repository = str(value or "").strip()
    parts = repository.split("/")
    if len(parts) != 2 or not all(_SEGMENT_RE.fullmatch(part) for part in parts):
        raise ValueError("repository must be a safe owner/repository pair.")
    return repository


def _workflow_id(value: object) -> str:
    workflow_id = str(value or "").strip()
    if not _WORKFLOW_RE.fullmatch(workflow_id):
        raise ValueError("workflow_id must be a numeric ID or workflow YAML filename.")
    return workflow_id


def _run_id(value: object) -> str:
    run_id = str(value or "").strip()
    if not re.fullmatch(r"[1-9][0-9]{0,18}", run_id):
        raise ValueError("run_id must be a positive numeric identifier.")
    return run_id


def _ref(value: object) -> str:
    ref = str(value or "").strip()
    if not ref or len(ref) > 255 or any(char in ref for char in "\r\n\x00"):
        raise ValueError("ref must be non-empty, at most 255 characters, and contain no control characters.")
    return ref


def _inputs(value: object) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict) or len(value) > 10:
        raise ValueError("inputs must be a dictionary with at most 10 values.")
    clean_inputs: dict[str, str] = {}
    for key, raw_value in value.items():
        name = str(key)
        text = str(raw_value)
        if not _SEGMENT_RE.fullmatch(name) or len(text) > 1024 or any(char in text for char in "\r\n\x00"):
            raise ValueError("workflow input names and values must be bounded and free of control characters.")
        clean_inputs[name] = text
    return clean_inputs


def _headers(token: str) -> dict[str, str]:
    access_token = str(token or "").strip()
    if not access_token or any(char in access_token for char in "\r\n\x00"):
        raise ValueError("A valid GitHub token is required.")
    return {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"}


async def _request(
    method: str,
    path: str,
    token: str,
    *,
    json_body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> httpx.Response:
    """Perform one GitHub API request without redirects and with a finite timeout."""
    async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
        return await client.request(
            method,
            f"{_BASE_URL}{path}",
            json=json_body,
            params=params,
            headers=_headers(token),
        )


async def run_action(repository: str, workflow_id: str, ref: str, inputs: dict, token: str) -> dict[str, Any]:
    """Dispatch a workflow using validated repository, workflow, ref, and input values."""
    response = await _request(
        "POST",
        f"/repos/{_repository(repository)}/actions/workflows/{_workflow_id(workflow_id)}/dispatches",
        token,
        json_body={"ref": _ref(ref), "inputs": _inputs(inputs)},
    )
    return {"status": "dispatched" if response.status_code == 204 else "error", "status_code": response.status_code}


async def list_workflows(repository: str, token: str) -> dict[str, Any]:
    """List at most 100 workflows for a validated repository."""
    response = await _request("GET", f"/repos/{_repository(repository)}/actions/workflows", token, params={"per_page": 100})
    return response.json()


async def get_workflow_run(repository: str, run_id: int, token: str) -> dict[str, Any]:
    """Get a validated workflow run."""
    response = await _request("GET", f"/repos/{_repository(repository)}/actions/runs/{_run_id(run_id)}", token)
    return response.json()


async def list_runs(repository: str, workflow_id: str, token: str) -> dict[str, Any]:
    """List at most 100 runs for a validated workflow."""
    response = await _request(
        "GET",
        f"/repos/{_repository(repository)}/actions/workflows/{_workflow_id(workflow_id)}/runs",
        token,
        params={"per_page": 100},
    )
    return response.json()


async def cancel_run(repository: str, run_id: int, token: str) -> dict[str, Any]:
    """Cancel a validated workflow run and expose the actual API status."""
    response = await _request("POST", f"/repos/{_repository(repository)}/actions/runs/{_run_id(run_id)}/cancel", token)
    return {"status": "cancelled" if response.status_code == 202 else "error", "status_code": response.status_code}
