# Autonomous Tool Synthesizer for HelloChusquis
# Converts capability gaps into working tool integrations
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from tools.base import Tool, ToolResult

console = Console()

TOOLS_DIR = Path(__file__).parent.parent / "tools"
TOOLS_DIR.mkdir(exist_ok=True)

def synthesize_basic_tool(service_name: str, description: str) -> bool:
    """
    Synthesize a basic REST API tool for a service.
    Returns True if successful, False otherwise.
    """
    file_name = re.sub(r"[^a-z0-9_]", "_", service_name.lower().strip("/"))
    tool_file = TOOLS_DIR / f"{file_name}.py"

    # Don't overwrite existing tools
    if tool_file.exists():
        console.print(f"[yellow]Tool '{service_name}' already exists at {tool_file}[/yellow]")
        return False

    console.print(f"[cyan]Synthesizing basic tool for {service_name}...[/cyan]")

    # Generate the tool code
    class_name = "".join(c for c in service_name.title() if c.isalnum()) + "Tool"
    
    tool_code = f'''from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from tools.base import Tool, ToolResult


class {class_name}(Tool):
    name = {file_name!r}
    description = {description!r}

    def run(self, action: str, **kwargs) -> ToolResult:
        """Execute an action against the {service_name} API."""
        api_key = self.config.get("api_key")
        if not api_key:
            return ToolResult(success=False, error=f"{service_name} API key not configured")

        base_url = self.config.get("base_url", "https://api.example.com/v1")
        headers = {{"Authorization": f"Bearer {{api_key}}", "Content-Type": "application/json"}}

        try:
            if action == "list":
                r = httpx.get(f"{{base_url}}", headers=headers, params=kwargs, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, data=r.json())

            elif action == "get":
                item_id = kwargs.get("id")
                if not item_id:
                    return ToolResult(success=False, error="ID required for get action")
                r = httpx.get(f"{{base_url}}/{{item_id}}", headers=headers, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, data=r.json())

            elif action == "create":
                data = kwargs.get("data", {{}})
                if not data:
                    return ToolResult(success=False, error="Data required for create action")
                r = httpx.post(f"{{base_url}}", headers=headers, json=data, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, data=r.json())

            elif action == "update":
                item_id = kwargs.get("id")
                if not item_id:
                    return ToolResult(success=False, error="ID required for update action")
                data = kwargs.get("data", {{}})
                if not data:
                    return ToolResult(success=False, error="Data required for update action")
                r = httpx.put(f"{{base_url}}/{{item_id}}", headers=headers, json=data, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, data=r.json())

            elif action == "delete":
                item_id = kwargs.get("id")
                if not item_id:
                    return ToolResult(success=False, error="ID required for delete action")
                r = httpx.delete(f"{{base_url}}/{{item_id}}", headers=headers, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, data={{}})

            else:
                return ToolResult(success=False, error=f"Unknown action: {{action}}")

        except httpx.HTTPStatusError as e:
            return ToolResult(success=False, error=f"HTTP {{e.response.status_code}}: {{e.response.text[:200]}}")
        except Exception as e:
            return ToolResult(success=False, error=f"Request failed: {{str(e)}}")

def run(action: str = "list", **kwargs):
    """Entry point for the tool."""
    tool = {class_name}()
    return tool.run(action, **kwargs)
'''

    # Validate the generated code by trying to compile it
    try:
        compile(tool_code, '<string>', 'exec')
    except SyntaxError as e:
        console.print(f"[red]Generated code has syntax error: {e}[/red]")
        return False

    # Save the tool
    try:
        tool_file.write_text(tool_code)
        console.print(f"[green]✓ Tool saved to {tool_file}[/green]")
        
        # Show the generated code
        syntax = Syntax(tool_code, "python", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title=f"Generated Tool: {file_name}", border_style="green"))
        
        return True
    except Exception as e:
        console.print(f"[red]Failed to save tool: {e}[/red]")
        return False

# ============================================================================
# TOOL SYNTHESIS 2.0: OpenAPI-powered intelligent tool generation
# ============================================================================

def synthesize_from_openapi(spec_source: str, service_name: str = None) -> bool:
    """
    Synthesize a tool from an OpenAPI/Swagger specification.
    
    This is the main entry point for Tool Synthesis 2.0. It parses the OpenAPI
    spec, extracts all endpoints, generates a complete Python tool with proper
    type hints and error handling.
    
    Args:
        spec_source: URL or file path to OpenAPI spec (JSON or YAML)
        service_name: Override service name (extracted from spec if not provided)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from core.openapi_parser import parse_openapi_spec
    except ImportError:
        console.print("[red]Error: core.openapi_parser not found. Please ensure it's installed.[/red]")
        return False
    
    console.print(f"[cyan]Loading OpenAPI spec from {spec_source}...[/cyan]")
    
    # Parse the spec
    parser = parse_openapi_spec(spec_source)
    if not parser:
        console.print("[red]Failed to parse OpenAPI specification.[/red]")
        return False
    
    # Extract service info
    info = parser.get_service_info()
    if not service_name:
        service_name = info['name']
    
    base_url = info['base_url']
    description = info['description']
    
    console.print(f"[green]✓ Parsed {parser.version}: {service_name} @ {base_url}[/green]")
    
    # Get auth scheme
    auth_type, auth_config = parser.get_auth_scheme()
    console.print(f"[dim]Auth: {auth_type} - {auth_config}[/dim]")
    
    # Get operations
    operations = parser.get_operations()
    # Audit #7: spec text is attacker-controlled. Sanitize every string
    # that gets embedded in generated code — newlines/control chars in a
    # summary or description can break out of comments/docstrings and
    # inject code into the generated tool.
    def _clean(text, limit=200):
        return re.sub(r"[\x00-\x1f\x7f`\\]", " ", str(text or ""))[:limit]

    for op in operations:
        op['operation_id'] = re.sub(r"[^A-Za-z0-9_]", "_", str(op.get('operation_id', '')))[:80]
        op['path'] = _clean(op.get('path', ''), 300)
        if op.get('summary'):
            op['summary'] = _clean(op['summary'])
        if op.get('description'):
            op['description'] = _clean(op['description'])
    console.print(f"[dim]Found {len(operations)} operations[/dim]")
    
    # Get suggested actions
    suggested_actions = parser.suggest_tool_actions()
    console.print(f"[dim]Suggested actions: {', '.join(suggested_actions)}[/dim]")
    
    # Generate the tool code
    # Audit #7: file_name comes from the spec title — strip everything
    # outside [a-z0-9_] so "../x" can't write outside tools/.
    file_name = re.sub(r"[^a-z0-9_]", "_", service_name.lower().strip("/"))
    tool_file = TOOLS_DIR / f"{file_name}.py"
    
    if tool_file.exists():
        console.print(f"[yellow]Tool '{service_name}' already exists at {tool_file}[/yellow]")
        console.print("[cyan]Use synthesize_from_openapi with overwrite=True to replace.[/cyan]")
        return False
    
    # Generate the tool
    tool_code = _generate_openapi_tool(
        service_name=service_name,
        file_name=file_name,
        base_url=base_url,
        description=description,
        auth_type=auth_type,
        auth_config=auth_config,
        operations=operations
    )
    
    # Validate and save
    try:
        compile(tool_code, '<string>', 'exec')
    except SyntaxError as e:
        console.print(f"[red]Generated code has syntax error: {e}[/red]")
        return False
    
    try:
        tool_file.write_text(tool_code)
        console.print(f"[green]✓ Tool saved to {tool_file}[/green]")
        
        syntax = Syntax(tool_code, "python", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title=f"Generated Tool: {file_name}", border_style="green"))
        
        # Auto-generate tests
        console.print("\n[cyan]Generating tests...[/cyan]")
        generate_tests_for_tool(service_name, file_name, operations, auth_type=auth_type)
        
        return True
    except Exception as e:
        console.print(f"[red]Failed to save tool: {e}[/red]")
        return False


def _generate_openapi_tool(
    service_name: str,
    file_name: str,
    base_url: str,
    description: str,
    auth_type: str,
    auth_config: Dict,
    operations: List[Dict]
) -> str:
    """Generate complete Python tool from OpenAPI operations."""
    
    class_name = "".join(c for c in service_name.title() if c.isalnum()) + "Tool"
    
    # Generate action handlers for each unique operation
    action_handlers = []
    
    # Group operations by their action type
    actions_by_type = {
        'list': [],
        'get': [],
        'create': [],
        'update': [],
        'delete': [],
        'search': [],
        'custom': []
    }
    
    for op in operations:
        method = op['method']
        path = op['path']
        op_id = op['operation_id']
        
        # Determine action type
        if method == 'GET' and '{' in path:
            action_type = 'get'
        elif method == 'GET':
            action_type = 'list'
        elif method == 'POST':
            action_type = 'create'
        elif method in ('PUT', 'PATCH'):
            action_type = 'update'
        elif method == 'DELETE':
            action_type = 'delete'
        elif 'search' in op_id.lower():
            action_type = 'search'
        else:
            action_type = 'custom'
        
        actions_by_type[action_type].append(op)
    
    # Build action handlers
    for action_type, ops in actions_by_type.items():
        if not ops:
            continue
        
        first_op = True
        for op in ops:
            path = op['path']
            op_id = op['operation_id']
            summary = op.get('summary', op.get('description', ''))[:100]
            params = op.get('parameters', [])
            
            # Build parameter handling
            path_params = [p['name'] for p in params if p.get('in') == 'path']
            query_params = [p['name'] for p in params if p.get('in') == 'query']
            
            # Path template for URL
            url_template = path.replace('{', '{').replace('}', '}')
            
            # First operation uses 'if', rest use 'elif'
            keyword = 'if' if first_op else 'elif'
            first_op = False
            
            handler = f'''            {keyword} action == "{op_id}":
                # {summary}
                url = f"{{base_url}}{path.replace('{', '{{').replace('}', '}}')}"
                params = {{}}
                for p in [{", ".join(repr(p) for p in query_params)}]:
                    if kwargs.get(p):
                        params[p] = kwargs.get(p)
                for p in [{", ".join(repr(p) for p in path_params)}]:
                    if kwargs.get(p):
                        url = url.replace('{{' + p + '}}', str(kwargs.get(p)))
                r = httpx.{op['method'].lower()}(url, headers=headers, params=params, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, output=json.dumps(r.json(), default=str), data=r.json())'''
            
            action_handlers.append(handler)
    
    # Add basic CRUD if not enough operations
    if len(action_handlers) < 3:
        basic_handlers = _get_basic_crud_handlers(service_name)
        action_handlers.extend(basic_handlers)
    
    action_handlers_code = "\n".join(action_handlers)
    all_op_ids = [op['operation_id'] for op in operations]

    # CRUD aliases: "list"/"get"/"create"/"update"/"delete" map to the first
    # matching operation so generic callers (and the helper methods below)
    # work without knowing operation ids.
    alias_map = {}
    for op in operations:
        method = op['method']
        path = op['path']
        if method == 'GET' and '{' in path:
            action_type = 'get'
        elif method == 'GET':
            action_type = 'list'
        elif method == 'POST':
            action_type = 'create'
        elif method in ('PUT', 'PATCH'):
            action_type = 'update'
        elif method == 'DELETE':
            action_type = 'delete'
        else:
            continue
        alias_map.setdefault(action_type, op['operation_id'])
    alias_lines = "\n".join(
        f'        "{atype}": "{opid}",' for atype, opid in alias_map.items()
    )
    
    # Generate auth setup
    auth_setup = _generate_auth_setup(auth_type, auth_config, service_name)
    
    tool_code = f'''"""
{description}
Generated from OpenAPI spec. {len(operations)} operations.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import httpx

from tools.base import Tool, ToolResult


class {class_name}(Tool):
    name = {file_name!r}
    description = {description!r}

    def run(self, action: str, **kwargs) -> ToolResult:
        """Execute an action against the {service_name} API."""
        {auth_setup}

        base_url = self.config.get("base_url", "{base_url}")

        # CRUD aliases → real operation ids
        action = {{
{alias_lines}
        }}.get(action, action)

        try:
{action_handlers_code}

            else:
                return ToolResult(success=False, error=f"Unknown action: {{action}}. Available actions: {', '.join(all_op_ids)}")

        except httpx.HTTPStatusError as e:
            return ToolResult(success=False, error=f"HTTP {{e.response.status_code}}: {{e.response.text[:200]}}")
        except httpx.TimeoutException:
            return ToolResult(success=False, error="Request timed out")
        except Exception as e:
            return ToolResult(success=False, error=f"Request failed: {{str(e)}}")

    def list(self, **kwargs) -> ToolResult:
        """List all resources."""
        return self.run("list", **kwargs)
    
    def get(self, id: str, **kwargs) -> ToolResult:
        """Get a specific resource by ID."""
        return self.run("get", id=id, **kwargs)
    
    def create(self, data: Dict, **kwargs) -> ToolResult:
        """Create a new resource."""
        return self.run("create", data=data, **kwargs)
    
    def update(self, id: str, data: Dict, **kwargs) -> ToolResult:
        """Update an existing resource."""
        return self.run("update", id=id, data=data, **kwargs)
    
    def delete(self, id: str, **kwargs) -> ToolResult:
        """Delete a resource."""
        return self.run("delete", id=id, **kwargs)


def run(action: str = "list", **kwargs):
    """Entry point for the tool."""
    tool = {class_name}()
    return tool.run(action, **kwargs)
'''
    
    return tool_code


def _generate_auth_setup(auth_type: str, auth_config: Dict, service_name: str) -> str:
    """Generate authentication setup code."""
    
    if auth_type == 'bearer':
        return '''api_key = self.config.get("api_key")
        if not api_key:
            return ToolResult(success=False, error=f"{service_name} API key not configured")
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}'''
    
    elif auth_type == 'api_key':
        header_name = auth_config.get('name', 'X-API-Key')
        return f'''api_key = self.config.get("api_key")
        if not api_key:
            return ToolResult(success=False, error=f"{service_name} API key not configured")
        headers = {{"{header_name}": api_key, "Content-Type": "application/json"}}'''
    
    elif auth_type == 'basic':
        return '''username = self.config.get("username")
        password = self.config.get("password")
        if not username or not password:
            return ToolResult(success=False, error=f"{service_name} credentials not configured")
        import base64
        auth = base64.b64encode(f"{{username}}:{{password}}".encode()).decode()
        headers = {{"Authorization": f"Basic {{auth}}", "Content-Type": "application/json"}}'''
    
    else:  # none
        return '''headers = {"Content-Type": "application/json"}'''


def _get_basic_crud_handlers(service_name: str) -> List[str]:
    """Generate basic CRUD handlers as fallback."""
    return [
        '''            if action == "list":
                r = httpx.get(f"{{base_url}}", headers=headers, params=kwargs, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, data=r.json())''',
        '''            if action == "get":
                item_id = kwargs.get("id")
                if not item_id:
                    return ToolResult(success=False, error="ID required for get action")
                r = httpx.get(f"{{base_url}}/{{item_id}}", headers=headers, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, data=r.json())''',
        '''            if action == "create":
                data = kwargs.get("data", {{}})
                if not data:
                    return ToolResult(success=False, error="Data required for create action")
                r = httpx.post(f"{{base_url}}", headers=headers, json=data, timeout=30)
                r.raise_for_status()
                return ToolResult(success=True, data=r.json())'''
    ]


def generate_tests_for_tool(
    service_name: str,
    file_name: str,
    operations: List[Dict],
    overwrite: bool = False,
    auth_type: str = "api_key",
) -> bool:
    """
    Auto-generate test cases for a synthesized tool.
    
    Creates a pytest-compatible test file with:
    - Basic initialization tests
    - Mock response tests for each operation
    - Error handling tests
    """
    test_dir = Path(__file__).parent.parent / "tests"
    test_dir.mkdir(exist_ok=True)
    
    test_file = test_dir / f"test_{file_name}.py"
    
    if test_file.exists() and not overwrite:
        console.print(f"[dim]Test file already exists: {test_file}[/dim]")
        return False
    
    class_name = "".join(c for c in service_name.title() if c.isalnum()) + "Tool"

    # Only tools with key-based auth can fail with "API key" errors
    if auth_type in ("api_key", "bearer"):
        missing_api_key_test = '''    def test_missing_api_key(self):
        """Test tool fails gracefully without API key."""
        tool = {class_name}()
        tool.config = {{}}

        result = tool.run("list")

        assert result.success is False
        assert "API key" in result.error
'''
    else:
        missing_api_key_test = ""

    # Generate test code
    test_code = f'''"""Auto-generated tests for {service_name} tool."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import httpx

from tools.{file_name} import {class_name}, run


class Test{class_name}:
    """Test cases for {service_name} API tool."""
    
    @pytest.fixture
    def tool(self):
        """Create tool instance with mock config."""
        tool = {class_name}()
        tool.config = {{
            "api_key": "test_key",
            "base_url": "https://api.test.com/v1"
        }}
        return tool
    
    def test_initialization(self, tool):
        """Test tool initializes correctly."""
        assert tool.name == "{file_name}"
        assert tool.description is not None
    
    def test_list_action(self, tool):
        """Test list action calls correct endpoint."""
        with patch('httpx.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {{"items": []}}
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            result = tool.run("list")
            
            assert result.success is True
            mock_get.assert_called_once()
    
    def test_get_action(self, tool):
        """Test get action retrieves specific item."""
        with patch('httpx.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {{"id": "123", "name": "test"}}
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            result = tool.run("get", id="123")
            
            assert result.success is True
            assert result.data.get("id") == "123"
    
    def test_create_action(self, tool):
        """Test create action posts data."""
        with patch('httpx.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {{"id": "456", "name": "new"}}
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response
            
            result = tool.run("create", data={{"name": "new"}})
            
            assert result.success is True
            mock_post.assert_called_once()
    
    {missing_api_key_test}
    def test_http_error_handling(self, tool):
        """Test tool handles HTTP errors correctly."""
        with patch('httpx.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Not Found"
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "404 Not Found", request=Mock(), response=mock_response
            )
            mock_get.return_value = mock_response
            
            result = tool.run("list")
            
            assert result.success is False
            assert "404" in result.error
    
    def test_timeout_handling(self, tool):
        """Test tool handles timeouts."""
        with patch('httpx.get') as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Request timed out")
            
            result = tool.run("list")
            
            assert result.success is False
            assert "timed out" in result.error
    
    def test_unknown_action(self, tool):
        """Test tool handles unknown actions."""
        result = tool.run("unknown_action")
        
        assert result.success is False
        assert "Unknown action" in result.error


class Test{class_name}Run:
    """Test the run() entry point function."""

    @pytest.fixture
    def tool(self):
        """Create tool instance with mock config."""
        tool = {class_name}()
        tool.config = {{
            "api_key": "test_key",
            "base_url": "https://api.test.com/v1"
        }}
        return tool

    def test_run_function_exists(self):
        """Test run function is callable."""
        assert callable(run)
    
    def test_run_with_list_action(self):
        """Test run function with list action."""
        with patch('tools.{file_name}.{class_name}.run') as mock_run:
            mock_run.return_value = Mock(success=True, data={{}})
            
            result = run("list")
            
            mock_run.assert_called_once_with("list")


# Additional operation-specific tests
'''
    
    # Add operation-specific tests
    for op in operations[:5]:  # Limit to first 5 to avoid huge files
        op_id = op['operation_id']
        method = op['method']
        
        test_code += f'''
    def test_{op_id}(self, tool):
        """Test {op['summary'] or op_id}."""
        with patch('httpx.{method.lower()}') as mock_call:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {{"success": True}}
            mock_response.raise_for_status = Mock()
            mock_call.return_value = mock_response
            
            result = tool.run("{op_id}")

            assert result.success is True
'''
    
    test_code += '''
# Make tests runnable with: pytest tests/test_<tool>.py -v
'''
    
    try:
        test_file.write_text(test_code)
        console.print(f"[green]✓ Tests saved to {test_file}[/green]")
        return True
    except Exception as e:
        console.print(f"[red]Failed to save tests: {e}[/red]")
        return False


# Keep the old interface for compatibility
def build_tool(tool_name: str = None):
    """Interactive tool builder - kept for backward compatibility."""
    console.print("[yellow]Note: Using autonomous tool synthesis instead of interactive builder.[/yellow]")
    console.print("[cyan]To synthesize a tool from OpenAPI, use: synthesize_from_openapi(spec_url, service_name)[/cyan]")
    console.print("[cyan]For basic tool, use: synthesize_basic_tool(service_name, description)[/cyan]")


def show_available_integrations():
    """Show available integrations that can be built."""
    console.print("[dim]Available synthesis modes:[/dim]")
    console.print("  - synthesize_basic_tool(name, desc): Basic CRUD template")
    console.print("  - synthesize_from_openapi(url, name): OpenAPI-powered intelligent synthesis")