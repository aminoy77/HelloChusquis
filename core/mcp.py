from __future__ import annotations

import asyncio
import re
from typing import Any
from dataclasses import dataclass, field


@dataclass
class MCPTransport:
    """Transport for MCP communication."""
    name: str = ""
    type: str = "stdio"  # stdio, http, websocket
    command: str = ""
    args: list[str] = field(default_factory=list)
    url: str = ""
    headers: dict = field(default_factory=dict)


@dataclass
class MCPTool:
    """A tool from MCP server."""
    name: str
    description: str
    input_schema: dict = field(default_factory=dict)


class MCPClient:
    """Model Context Protocol client for connecting to external tools."""
    
    def __init__(self):
        self.servers: dict[str, MCPTransport] = {}
        self.tools: dict[str, MCPTool] = {}
        self._process: Any = None
    
    def add_server(self, name: str, transport: MCPTransport):
        """Add an MCP server."""
        self.servers[name] = transport
    
    async def connect(self, name: str) -> dict:
        """Connect to an MCP server."""
        transport = self.servers.get(name)
        if not transport:
            return {"success": False, "error": f"Server not found: {name}"}
        
        if transport.type == "stdio":
            try:
                import subprocess
                cmd = [transport.command] + transport.args
                self._process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                return {"success": True, "server": name}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": f"Unsupported transport: {transport.type}"}
    
    async def call_tool(self, server: str, tool_name: str, arguments: dict) -> dict:
        """Call a tool on an MCP server."""
        if not self._process:
            return {"success": False, "error": "Not connected"}
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        import json
        try:
            self._process.stdin.write(json.dumps(request).encode() + b"\n")
            self._process.stdin.flush()
            
            response = self._process.stdout.readline()
            return {"success": True, "data": json.loads(response)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_tools(self, server: str = None) -> list[dict]:
        """List available tools."""
        return [
            {"server": server, "name": t.name, "description": t.description}
            for server, tools in self.tools.items()
            for t in tools
        ]
    
    async def disconnect(self):
        """Disconnect from all servers."""
        if self._process:
            self._process.terminate()
            self._process = None


# Common MCP servers configuration
DEFAULT_MCP_SERVERS = {
    "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    },
    "git": {
        "command": "npx", 
        "args": ["-y", "@modelcontextprotocol/server-git"]
    },
    "github": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"]
    },
    "slack": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-slack"]
    },
    "postgres": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-postgres"]
    }
}


_client = None

def get_client() -> MCPClient:
    global _client
    if _client is None:
        _client = MCPClient()
    return _client