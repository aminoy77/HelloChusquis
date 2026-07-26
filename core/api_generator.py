# DEPRECATED: This module is not used. Consider removing.
from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class APIEndpoint:
    method: str
    path: str
    description: str
    params: list[str]
    auth_required: bool = True


class APIGenerator:
    """Generate API endpoints and documentation from code."""

    def __init__(self):
        self.endpoints: list[APIEndpoint] = []

    def analyze_fastapi(self, file_path: str) -> list[APIEndpoint]:
        """Analyze FastAPI file and extract endpoints."""
        endpoints = []
        
        try:
            with open(file_path) as f:
                content = f.read()
        except Exception:
            return endpoints

        import re
        
        # Match @app.get("/path"), @router.get("/path"), etc.
        pattern = r'@(?:app|router)\.(\w+)\(["\']([^"\']+)["\']\)'
        matches = re.finditer(pattern, content)

        for match in matches:
            method = match.group(1).upper()
            path = match.group(2)
            
            # Find description from next line or docstring
            lines = content[match.end():match.end()+500].split('\n')
            description = ""
            for line in lines[:5]:
                if line.strip() and not line.strip().startswith('def '):
                    description = line.strip().strip('"\' ')
                    break
            
            endpoints.append(APIEndpoint(
                method=method,
                path=path,
                description=description or f"{method} {path}",
                params=self._extract_params(content, path),
                auth_required='Depends' in content[match.start():match.start()+300]
            ))

        self.endpoints = endpoints
        return endpoints

    def _extract_params(self, content: str, path: str) -> list[str]:
        """Extract path parameters from endpoint."""
        import re
        params = re.findall(r'\{(\w+)\}', path)
        return params

    def generate_openapi(self) -> dict:
        """Generate OpenAPI spec from endpoints."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Generated API", "version": "1.0.0"},
            "paths": {}
        }

        for ep in self.endpoints:
            if ep.path not in spec["paths"]:
                spec["paths"][ep.path] = {}

            spec["paths"][ep.path][ep.method.lower()] = {
                "summary": ep.description,
                "parameters": [
                    {"name": p, "in": "path", "required": True}
                    for p in ep.params
                ],
                "responses": {"200": {"description": "OK"}}
            }

        return spec

    def generate_docs(self) -> str:
        """Generate Markdown documentation."""
        lines = ["# API Documentation", ""]

        # Group by path
        by_path = {}
        for ep in self.endpoints:
            if ep.path not in by_path:
                by_path[ep.path] = []
            by_path[ep.path].append(ep)

        for path, eps in sorted(by_path.items()):
            lines.append(f"## `{path}`")
            
            for ep in eps:
                auth = "🔒" if ep.auth_required else "🔓"
                lines.append(f"### {ep.method} {auth}")
                lines.append(f"{ep.description}")
                
                if ep.params:
                    lines.append("**Parameters:**")
                    for p in ep.params:
                        lines.append(f"- `{p}`")
                
                lines.append("")

        return "\n".join(lines)

    def generate_postman_collection(self) -> dict:
        """Generate Postman collection."""
        return {
            "info": {"name": "Generated API", "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"},
            "item": [
                {
                    "name": ep.path,
                    "request": {
                        "method": ep.method,
                        "url": {"raw": f"{{base_url}}{ep.path}"}
                    }
                }
                for ep in self.endpoints
            ]
        }


def get_generator() -> APIGenerator:
    return APIGenerator()