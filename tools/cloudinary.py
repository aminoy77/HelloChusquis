from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional
from tools.base import Tool, ToolResult


class CloudinaryTool(Tool):
    name = "cloudinary"
    description = "Cloudinary - image and video management"

    def run(self, action: str, **kwargs) -> ToolResult:
        cloud_name = self.config.get("cloud_name")
        api_key = self.config.get("api_key")
        api_secret = self.config.get("api_secret")

        if not cloud_name or not api_key:
            return ToolResult(success=False, error="Cloudinary credentials not configured")

        base_url = f"https://res.cloudinary.com/{cloud_name}"

        try:
            if action == "upload":
                file = kwargs.get("file")
                if not file:
                    return ToolResult(success=False, error="File URL or data required")
                payload = {
                    "file": file,
                    "api_key": api_key,
                    "timestamp": kwargs.get("timestamp", ""),
                    "tags": kwargs.get("tags", ""),
                    "folder": kwargs.get("folder", "")
                }
                r = httpx.post(f"{base_url}/image/upload", params=payload, timeout=60)
                return ToolResult(success=True, data=r.json())

            elif action == "list_resources":
                r = httpx.get(f"{base_url}/resources/image", params={"api_key": api_key}, timeout=30)
                data = r.json()
                return ToolResult(success=True, data=data.get("resources", []))

            elif action == "delete_resource":
                public_id = kwargs.get("public_id")
                if not public_id:
                    return ToolResult(success=False, error="Public ID required")
                payload = {"public_id": public_id, "api_key": api_key}
                r = httpx.post(f"{base_url}/image/destroy", params=payload, timeout=30)
                return ToolResult(success=True, data=r.json())

            elif action == "transform":
                public_id = kwargs.get("public_id")
                if not public_id:
                    return ToolResult(success=False, error="Public ID required")
                transformations = kwargs.get("transformations", "c_fill,w_500,h_500")
                url = f"{base_url}/image/upload/{transformations}/{public_id}"
                return ToolResult(success=True, data={"url": url})

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))