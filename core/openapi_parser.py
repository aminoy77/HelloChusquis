"""OpenAPI/Swagger specification parser for intelligent tool synthesis."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import httpx
import yaml


class OpenAPIParser:
    """Parse OpenAPI 3.0 and Swagger 2.0 specifications."""
    
    def __init__(self, spec_source: str):
        """
        Initialize parser with spec URL or file path.
        
        Args:
            spec_source: URL to OpenAPI spec or local file path
        """
        self.spec_source = spec_source
        self.spec: Dict[str, Any] = {}
        self.version: str = ""
        
    def load_spec(self) -> bool:
        """Load and parse the OpenAPI specification."""
        try:
            if self._is_url(self.spec_source):
                return self._load_from_url()
            else:
                return self._load_from_file()
        except Exception as e:
            print(f"Failed to load spec: {e}")
            return False
    
    def _is_url(self, source: str) -> bool:
        """Check if source is a URL."""
        parsed = urlparse(source)
        return parsed.scheme in ('http', 'https')
    
    def _load_from_url(self) -> bool:
        """Download spec from URL."""
        try:
            response = httpx.get(self.spec_source, timeout=10, follow_redirects=True)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '')
            if 'json' in content_type:
                self.spec = response.json()
            else:
                self.spec = yaml.safe_load(response.text)
            
            self._detect_version()
            return True
        except Exception as e:
            print(f"Failed to download spec: {e}")
            return False
    
    def _load_from_file(self) -> bool:
        """Load spec from local file."""
        try:
            path = Path(self.spec_source).expanduser()
            content = path.read_text()
            
            if path.suffix in ('.yaml', '.yml'):
                self.spec = yaml.safe_load(content)
            else:
                self.spec = json.loads(content)
            
            self._detect_version()
            return True
        except Exception as e:
            print(f"Failed to load spec file: {e}")
            return False
    
    def _detect_version(self):
        """Detect OpenAPI/Swagger version."""
        if 'openapi' in self.spec:
            self.version = f"OpenAPI {self.spec['openapi']}"
        elif 'swagger' in self.spec:
            self.version = f"Swagger {self.spec['swagger']}"
        else:
            self.version = "Unknown"
    
    def get_service_info(self) -> Dict[str, str]:
        """Extract basic service information."""
        info = self.spec.get('info', {})
        return {
            'name': info.get('title', 'Unknown Service'),
            'description': info.get('description', ''),
            'version': info.get('version', '1.0.0'),
            'base_url': self._get_base_url()
        }
    
    def _get_base_url(self) -> str:
        """Extract base URL from spec."""
        # OpenAPI 3.0
        servers = self.spec.get('servers', [])
        if servers and isinstance(servers, list):
            return servers[0].get('url', 'https://api.example.com')
        
        # Swagger 2.0
        host = self.spec.get('host', 'api.example.com')
        schemes = self.spec.get('schemes', ['https'])
        base_path = self.spec.get('basePath', '')
        return f"{schemes[0]}://{host}{base_path}"
    
    def get_auth_scheme(self) -> Tuple[str, Dict[str, Any]]:
        """
        Detect authentication scheme.
        
        Returns:
            (auth_type, auth_config) tuple
            auth_type: 'bearer', 'api_key', 'oauth2', 'basic', or 'none'
        """
        # OpenAPI 3.0
        components = self.spec.get('components', {})
        security_schemes = components.get('securitySchemes', {})
        
        # Swagger 2.0
        if not security_schemes:
            security_schemes = self.spec.get('securityDefinitions', {})
        
        if not security_schemes:
            return ('none', {})
        
        # Get first security scheme
        scheme_name, scheme = next(iter(security_schemes.items()))
        scheme_type = scheme.get('type', 'apiKey')
        
        if scheme_type == 'http':
            http_scheme = scheme.get('scheme', 'bearer')
            return (http_scheme, {'header': 'Authorization'})
        elif scheme_type == 'apiKey':
            return ('api_key', {
                'name': scheme.get('name', 'X-API-Key'),
                'in': scheme.get('in', 'header')
            })
        elif scheme_type == 'oauth2':
            return ('oauth2', {'flows': scheme.get('flows', {})})
        else:
            return ('none', {})
    
    def get_operations(self) -> List[Dict[str, Any]]:
        """
        Extract all API operations (endpoints).
        
        Returns:
            List of operation dicts with:
            - operation_id: Unique operation identifier
            - method: HTTP method (get, post, etc.)
            - path: Endpoint path
            - summary: Brief description
            - parameters: List of parameters
            - request_body: Request schema (if applicable)
            - responses: Response schemas
        """
        operations = []
        paths = self.spec.get('paths', {})
        
        for path, path_item in paths.items():
            for method in ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']:
                if method not in path_item:
                    continue
                
                operation = path_item[method]
                
                # Extract operation details
                op_data = {
                    'operation_id': operation.get('operationId', f"{method}_{path.replace('/', '_')}"),
                    'method': method.upper(),
                    'path': path,
                    'summary': operation.get('summary', ''),
                    'description': operation.get('description', ''),
                    'parameters': self._extract_parameters(operation.get('parameters', [])),
                    'request_body': self._extract_request_body(operation.get('requestBody')),
                    'responses': self._extract_responses(operation.get('responses', {}))
                }
                
                operations.append(op_data)
        
        return operations
    
    def _extract_parameters(self, params: List[Dict]) -> List[Dict[str, Any]]:
        """Extract parameter information."""
        extracted = []
        for param in params:
            extracted.append({
                'name': param.get('name', ''),
                'in': param.get('in', 'query'),
                'required': param.get('required', False),
                'type': self._get_param_type(param),
                'description': param.get('description', '')
            })
        return extracted
    
    def _get_param_type(self, param: Dict) -> str:
        """Get parameter type from schema."""
        schema = param.get('schema', {})
        if schema:
            return schema.get('type', 'string')
        return param.get('type', 'string')
    
    def _extract_request_body(self, body: Optional[Dict]) -> Optional[Dict[str, Any]]:
        """Extract request body schema."""
        if not body:
            return None
        
        content = body.get('content', {})
        if 'application/json' in content:
            schema = content['application/json'].get('schema', {})
            return {
                'required': body.get('required', False),
                'schema': schema
            }
        return None
    
    def _extract_responses(self, responses: Dict) -> Dict[str, Any]:
        """Extract response schemas."""
        extracted = {}
        for status_code, response in responses.items():
            content = response.get('content', {})
            if 'application/json' in content:
                schema = content['application/json'].get('schema', {})
                extracted[status_code] = {
                    'description': response.get('description', ''),
                    'schema': schema
                }
        return extracted
    
    def suggest_tool_actions(self) -> List[str]:
        """
        Suggest high-level action names based on operations.
        
        Groups similar operations into logical actions like:
        - list, get, create, update, delete (CRUD)
        - search, upload, download (common patterns)
        """
        operations = self.get_operations()
        actions = set()
        
        for op in operations:
            method = op['method']
            path = op['path']
            op_id = op['operation_id'].lower()
            
            # CRUD detection
            if method == 'GET':
                if '{' in path:
                    actions.add('get')
                else:
                    actions.add('list')
            elif method == 'POST':
                actions.add('create')
            elif method in ('PUT', 'PATCH'):
                actions.add('update')
            elif method == 'DELETE':
                actions.add('delete')
            
            # Pattern detection
            if 'search' in op_id:
                actions.add('search')
            if 'upload' in op_id:
                actions.add('upload')
            if 'download' in op_id:
                actions.add('download')
        
        return sorted(list(actions))


def parse_openapi_spec(spec_source: str) -> Optional[OpenAPIParser]:
    """
    Parse an OpenAPI specification and return parser object.
    
    Args:
        spec_source: URL or file path to OpenAPI spec
        
    Returns:
        OpenAPIParser instance if successful, None otherwise
    """
    parser = OpenAPIParser(spec_source)
    if parser.load_spec():
        return parser
    return None
