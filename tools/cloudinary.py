"""Cloudinary image and video management integration."""

from __future__ import annotations

import hashlib
import os
import re
import time
from urllib.parse import quote

import httpx

PLUGIN_NAME = "cloudinary"
PLUGIN_DESCRIPTION = "Cloudinary - image and video management"

_CLOUD_NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,255}$")
MAX_CLOUDINARY_LIST_RESULTS = 100


def _sign(params: dict, api_secret: str) -> str:
    """Build a SHA-256 Cloudinary API signature for signed requests."""
    parts = "&".join(f"{key}={value}" for key, value in sorted(params.items()))
    return hashlib.sha256((parts + api_secret).encode("utf-8")).hexdigest()


def _bounded_max_results(value: object) -> int:
    """Normalize resource-list limits before they reach the provider."""
    try:
        maximum = int(value)
    except (TypeError, ValueError):
        return 50
    return max(1, min(maximum, MAX_CLOUDINARY_LIST_RESULTS))


def _safe_cloud_name(value: object) -> str | None:
    cloud_name = str(value or "")
    return cloud_name if _CLOUD_NAME_RE.fullmatch(cloud_name) else None


def _safe_public_id(value: object) -> str | None:
    public_id = str(value or "")
    if not public_id or len(public_id) > 1024 or "\x00" in public_id:
        return None
    if any(part in {".", ".."} for part in public_id.split("/")):
        return None
    return public_id


def run(action: str, **kwargs) -> str:
    cloud_name = _safe_cloud_name(os.getenv("CLOUDINARY_CLOUD_NAME"))
    api_key = os.getenv("CLOUDINARY_API_KEY")
    api_secret = os.getenv("CLOUDINARY_API_SECRET")
    if not cloud_name:
        return "Error: Invalid Cloudinary cloud name."
    if not api_key:
        return "Error: Cloudinary credentials not configured. Set CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY environment variables."

    api_base = f"https://api.cloudinary.com/v1_1/{cloud_name}/image"
    try:
        if action == "upload":
            file = kwargs.get("file")
            if not isinstance(file, str) or not file or len(file) > 4096:
                return "Error: file (URL or path) required for upload"
            params = {
                "file": file,
                "api_key": api_key,
                "timestamp": kwargs.get("timestamp") or str(int(time.time())),
                "folder": kwargs.get("folder", ""),
            }
            if api_secret:
                params["signature"] = _sign(params, api_secret)
            response = httpx.post(
                f"{api_base}/upload",
                data=params,
                timeout=60,
                follow_redirects=False,
            )
            return _fmt(response)

        if action == "list_resources":
            params = {"api_key": api_key, "max_results": _bounded_max_results(kwargs.get("max_results", 50))}
            if api_secret:
                params["timestamp"] = str(int(time.time()))
                params["signature"] = _sign(params, api_secret)
            response = httpx.get(
                f"{api_base}/resources",
                params=params,
                timeout=30,
                follow_redirects=False,
            )
            response.raise_for_status()
            data = response.json()
            return str(data.get("resources", data))

        if action == "delete_resource":
            public_id = _safe_public_id(kwargs.get("public_id"))
            if not public_id:
                return "Error: valid public_id required for delete_resource"
            params = {"public_id": public_id, "api_key": api_key, "timestamp": str(int(time.time()))}
            if api_secret:
                params["signature"] = _sign(params, api_secret)
            response = httpx.post(
                f"{api_base}/destroy",
                data=params,
                timeout=30,
                follow_redirects=False,
            )
            return _fmt(response)

        if action == "transform":
            public_id = _safe_public_id(kwargs.get("public_id"))
            if not public_id:
                return "Error: valid public_id required for transform"
            transformations = str(kwargs.get("transformations", "c_fill,w_500,h_500"))
            if len(transformations) > 2048 or "\x00" in transformations:
                return "Error: invalid transformations"
            safe_transformations = quote(transformations, safe="/,;:_-")
            safe_public_id = quote(public_id, safe="/-_.")
            url = f"https://res.cloudinary.com/{cloud_name}/image/upload/{safe_transformations}/{safe_public_id}"
            return f"Transformed URL: {url}"

        return "Error: Unknown action. Available: upload, list_resources, delete_resource, transform"
    except httpx.TimeoutException:
        return "Error: Request timed out."
    except httpx.HTTPError as exc:
        return f"Error: {exc}"


def _fmt(response: httpx.Response) -> str:
    response.raise_for_status()
    try:
        return str(response.json())
    except ValueError:
        return response.text[:500]
