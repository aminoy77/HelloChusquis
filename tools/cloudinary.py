from __future__ import annotations

import os
import time
import hashlib
import httpx

PLUGIN_NAME = "cloudinary"
PLUGIN_DESCRIPTION = "Cloudinary - image and video management"


def _sign(params: dict, api_secret: str) -> str:
    """Build a SHA-256 Cloudinary API signature for signed requests."""
    parts = "&".join(f"{key}={value}" for key, value in sorted(params.items()))
    return hashlib.sha256((parts + api_secret).encode("utf-8")).hexdigest()


def run(action: str, **kwargs) -> str:
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    api_key = os.getenv("CLOUDINARY_API_KEY")
    api_secret = os.getenv("CLOUDINARY_API_SECRET")
    if not cloud_name or not api_key:
        return "Error: Cloudinary credentials not configured. Set CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY environment variables."

    try:
        if action == "upload":
            file = kwargs.get("file")
            if not file:
                return "Error: file (URL or path) required for upload"
            params = {
                "file": file,
                "api_key": api_key,
                "timestamp": kwargs.get("timestamp") or str(int(time.time())),
                "folder": kwargs.get("folder", ""),
            }
            if api_secret:
                params["signature"] = _sign(params, api_secret)
            r = httpx.post(f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload", data=params, timeout=60)
            return _fmt(r)

        elif action == "list_resources":
            params = {"api_key": api_key, "max_results": kwargs.get("max_results", 50)}
            if api_secret:
                params["timestamp"] = str(int(time.time()))
                params["signature"] = _sign(params, api_secret)
            r = httpx.get(f"https://api.cloudinary.com/v1_1/{cloud_name}/resources/image", params=params, timeout=30)
            data = r.json()
            return str(data.get("resources", data))

        elif action == "delete_resource":
            public_id = kwargs.get("public_id")
            if not public_id:
                return "Error: public_id required for delete_resource"
            params = {"public_id": public_id, "api_key": api_key, "timestamp": str(int(time.time()))}
            if api_secret:
                params["signature"] = _sign(params, api_secret)
            r = httpx.post(f"https://api.cloudinary.com/v1_1/{cloud_name}/image/destroy", data=params, timeout=30)
            return _fmt(r)

        elif action == "transform":
            public_id = kwargs.get("public_id")
            if not public_id:
                return "Error: public_id required for transform"
            transformations = kwargs.get("transformations", "c_fill,w_500,h_500")
            url = f"https://res.cloudinary.com/{cloud_name}/image/upload/{transformations}/{public_id}"
            return f"Transformed URL: {url}"

        else:
            return f"Error: Unknown action '{action}'. Available: upload, list_resources, delete_resource, transform"
    except httpx.TimeoutException:
        return "Error: Request timed out."
    except Exception as e:
        return f"Error: {e}"


def _fmt(r: httpx.Response) -> str:
    try:
        return str(r.json())
    except Exception:
        return r.text[:500]