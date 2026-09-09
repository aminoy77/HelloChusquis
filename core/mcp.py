"""
MCP (Model Context Protocol) implementation for HelloChusquis.

Implements the Model Context Protocol. Provides:
- Transport classes (Stdio, HTTP, SSE)
- MCPServer: host MCP server exposing tools via JSON-RPC 2.0
- MCPClient: connect to multiple MCP servers, auto-discover tools
- MCPToolBridge: bridge MCP tools ↔ agent tools
- MCPServerConfig: server config, capability negotiation, security policies
"""

from __future__ import annotations

import asyncio
from collections import deque
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from urllib.parse import urlsplit

from tools.web_fetch import SsrFBlockedError, validate_url_safety

logger = logging.getLogger(__name__)

MCP_STDIO_MAX_DIAGNOSTIC_LINES = 100
MCP_STDIO_MAX_LINE_BYTES = 65_536
MCP_STDIO_STOP_TIMEOUT_SECONDS = 5
_DEFAULT_MCP_FILESYSTEM_DIRECTORY = Path.home() / ".hellochusquis" / "mcp-files"


def _ensure_default_filesystem_workspace(root: Path | None = None) -> Path:
    """Create the owner-only filesystem root used by the default MCP server."""
    workspace = root or _DEFAULT_MCP_FILESYSTEM_DIRECTORY
    if workspace.is_symlink():
        raise ValueError("default MCP filesystem workspace must not be a symlink")
    workspace.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(workspace, 0o700)
    return workspace


def validate_mcp_remote_url(url: str) -> str:
    """Accept only public HTTPS endpoints for remote MCP transports."""
    if not isinstance(url, str) or not url.strip():
        raise ValueError("MCP remote URL is required")
    normalized = url.strip()
    parsed = urlsplit(normalized)
    if parsed.scheme != "https":
        raise ValueError("MCP remote URL must use HTTPS")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("MCP remote URL must not include credentials")
    try:
        return validate_url_safety(normalized)
    except (SsrFBlockedError, ValueError) as exc:
        raise ValueError("MCP remote URL is unsafe") from exc


# ---------------------------------------------------------------------------
# JSON-RPC 2.0 helpers
# ---------------------------------------------------------------------------

class JSONRPCError(Exception):
    """JSON-RPC 2.0 error with code + message + optional data."""

    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)

    def to_dict(self) -> dict:
        err: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.data is not None:
            err["data"] = self.data
        return err


class ParseError(JSONRPCError):
    def __init__(self, data: Any = None):
        super().__init__(-32700, "Parse error", data)


class InvalidRequest(JSONRPCError):
    def __init__(self, data: Any = None):
        super().__init__(-32600, "Invalid request", data)


class MethodNotFound(JSONRPCError):
    def __init__(self, method: str):
        super().__init__(-32601, f"Method not found: {method}")


class InvalidParams(JSONRPCError):
    def __init__(self, message: str = "Invalid params"):
        super().__init__(-32602, message)


class InternalError(JSONRPCError):
    def __init__(self, message: str = "Internal error", data: Any = None):
        super().__init__(-32603, message, data)


def jsonrpc_response(req_id: Any, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def jsonrpc_error_response(req_id: Any, error: JSONRPCError) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": error.to_dict()}


def jsonrpc_request(method: str, params: Any = None, req_id: Any = None) -> dict:
    msg: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
    if req_id is not None:
        msg["id"] = req_id
    if params is not None:
        msg["params"] = params
    return msg


def jsonrpc_notification(method: str, params: Any = None) -> dict:
    msg: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        msg["params"] = params
    return msg


# ---------------------------------------------------------------------------
# Transport layer (abstract + concrete)
# ---------------------------------------------------------------------------

class MCPTransport(ABC):
    """Abstract transport for MCP JSON-RPC communication."""

    def __init__(self, name: str = "", transport_type: str = "abstract"):
        self.name = name
        self.transport_type = transport_type

    @abstractmethod
    async def connect(self) -> None:
        """Open the transport channel."""

    @abstractmethod
    async def send(self, message: dict) -> None:
        """Send a JSON-RPC message."""

    @abstractmethod
    async def receive(self) -> Optional[dict]:
        """Receive a JSON-RPC message. Returns None on EOF."""

    @abstractmethod
    async def close(self) -> None:
        """Close the transport channel."""

    @property
    def is_connected(self) -> bool:
        return False

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *exc):
        await self.close()


class StdioTransport(MCPTransport):
    """Communicate with an MCP server via stdin/stdout subprocess."""

    def __init__(
        self,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        cwd: str | None = None,
        name: str = "",
    ):
        super().__init__(name=name or command, transport_type="stdio")
        self.command = command
        self.args = args or []
        self.env = env
        self.cwd = cwd
        self._process: Optional[subprocess.Popen[bytes]] = None
        self._connected = False
        self._stderr_lines: deque[str] = deque(maxlen=MCP_STDIO_MAX_DIAGNOSTIC_LINES)
        self._stderr_task: Optional[asyncio.Task[None]] = None

    @property
    def is_connected(self) -> bool:
        return self._connected and self._process is not None and self._process.poll() is None

    async def connect(self) -> None:
        if self._connected:
            return
        loop = asyncio.get_event_loop()
        # Resolve the executable before spawning, but pass only explicitly
        # configured variables to avoid leaking host credentials into a server.
        command = self.command
        if not os.path.isabs(command):
            command = shutil.which(command) or command
        process_env = dict(self.env or {})
        self._process = await loop.run_in_executor(
            None,
            lambda: subprocess.Popen(
                [command] + self.args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=process_env,
                cwd=self.cwd,
            ),
        )
        self._connected = True
        # Capture stderr in background
        self._stderr_task = asyncio.create_task(self._drain_stderr())

    async def _drain_stderr(self) -> None:
        if not self._process or not self._process.stderr:
            return
        loop = asyncio.get_event_loop()
        try:
            while True:
                line = await loop.run_in_executor(
                    None, self._process.stderr.readline, MCP_STDIO_MAX_LINE_BYTES
                )
                if not line:
                    break
                decoded = line.decode("utf-8", errors="replace").rstrip()
                if decoded:
                    self._stderr_lines.append(decoded)
                    logger.debug("mcp stderr [%s]: %s", self.name, decoded)
        except Exception:
            pass

    async def send(self, message: dict) -> None:
        if not self.is_connected or not self._process or not self._process.stdin:
            raise ConnectionError("StdioTransport not connected")
        payload = json.dumps(message) + "\n"
        raw = payload.encode("utf-8")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._process.stdin.write, raw)
        await loop.run_in_executor(None, self._process.stdin.flush)

    async def receive(self) -> Optional[dict]:
        if not self.is_connected or not self._process or not self._process.stdout:
            return None
        loop = asyncio.get_event_loop()
        line = await loop.run_in_executor(
            None, self._process.stdout.readline, MCP_STDIO_MAX_LINE_BYTES
        )
        if not line:
            return None
        if len(line) >= MCP_STDIO_MAX_LINE_BYTES and not line.endswith(b"\n"):
            raise ParseError("MCP stdio response exceeds the line-size limit")
        text = line.decode("utf-8", errors="replace").strip()
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            raise ParseError(f"Invalid JSON: {text[:200]}")

    async def close(self) -> None:
        self._connected = False
        if self._stderr_task and not self._stderr_task.done():
            self._stderr_task.cancel()
            try:
                await self._stderr_task
            except asyncio.CancelledError:
                pass
        if self._process:
            try:
                self._process.terminate()
                try:
                    self._process.wait(timeout=MCP_STDIO_STOP_TIMEOUT_SECONDS)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                    self._process.wait(timeout=MCP_STDIO_STOP_TIMEOUT_SECONDS)
            except Exception:
                pass
            for stream in (self._process.stdin, self._process.stdout, self._process.stderr):
                if stream is not None:
                    stream.close()
            self._process = None


class HTTPTransport(MCPTransport):
    """Communicate with an MCP server via HTTP POST (JSON-RPC over HTTP)."""

    def __init__(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        name: str = "",
        timeout: float = 30.0,
    ):
        safe_url = validate_mcp_remote_url(url).rstrip("/")
        super().__init__(name=name or safe_url, transport_type="http")
        self.url = safe_url
        self.headers = headers or {}
        self.timeout = timeout
        self._connected = False
        self._session: Any = None  # aiohttp.ClientSession or httpx.AsyncClient
        self._request_id = 0

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def connect(self) -> None:
        if self._connected:
            return
        try:
            import aiohttp
            self._session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                raise_for_status=False,
            )
        except ImportError:
            import httpx
            self._session = httpx.AsyncClient(
                headers=self.headers, timeout=self.timeout, follow_redirects=False
            )
        self._connected = True

    async def send(self, message: dict) -> None:
        """POST a JSON-RPC message; for HTTP transport we also await the response inline."""
        if not self._connected or self._session is None:
            raise ConnectionError("HTTPTransport not connected")
        payload = json.dumps(message)
        if hasattr(self._session, "post"):
            # aiohttp or httpx
            try:
                import aiohttp
                if isinstance(self._session, aiohttp.ClientSession):
                    async with self._session.post(
                        self.url,
                        data=payload,
                        content_type="application/json",
                        allow_redirects=False,
                    ) as resp:
                        body = await resp.text()
                        self._last_response = json.loads(body) if body.strip() else None
                        return
            except ImportError:
                pass
            import httpx
            if isinstance(self._session, httpx.AsyncClient):
                resp = await self._session.post(self.url, content=payload)
                body = resp.text
                self._last_response = json.loads(body) if body.strip() else None
                return
        raise RuntimeError("No HTTP client available")

    async def receive(self) -> Optional[dict]:
        """Return the last response captured by send()."""
        return getattr(self, "_last_response", None)

    async def call(self, method: str, params: Any = None) -> Any:
        """Convenience: send request + return result, raising JSONRPCError on failure."""
        req_id = self._next_id()
        msg = jsonrpc_request(method, params, req_id)
        await self.send(msg)
        resp = await self.receive()
        if resp is None:
            raise InternalError("No response from server")
        if "error" in resp:
            err = resp["error"]
            raise JSONRPCError(err.get("code", -32603), err.get("message", "Unknown"), err.get("data"))
        return resp.get("result")

    async def close(self) -> None:
        self._connected = False
        if self._session and hasattr(self._session, "close"):
            await self._session.close()
        self._session = None


class SSETransport(MCPTransport):
    """Server-Sent Events transport: POST requests, SSE stream for server→client."""

    def __init__(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        name: str = "",
        timeout: float = 60.0,
    ):
        safe_url = validate_mcp_remote_url(url).rstrip("/")
        super().__init__(name=name or safe_url, transport_type="sse")
        self.url = safe_url
        self.headers = headers or {}
        self.timeout = timeout
        self._connected = False
        self._session: Any = None
        self._event_stream_task: Optional[asyncio.Task[None]] = None
        self._incoming: asyncio.Queue[Optional[dict]] = asyncio.Queue()
        self._request_id = 0

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def connect(self) -> None:
        if self._connected:
            return
        try:
            import aiohttp
            self._session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                raise_for_status=False,
            )
            self._use_aiohttp = True
        except ImportError:
            import httpx
            self._session = httpx.AsyncClient(
                headers=self.headers, timeout=self.timeout, follow_redirects=False
            )
            self._use_aiohttp = False
        self._connected = True
        # Start background SSE listener
        self._event_stream_task = asyncio.create_task(self._listen_sse())

    async def _listen_sse(self) -> None:
        """Background task that reads the SSE event stream and enqueues parsed JSON."""
        sse_url = self.url
        # For SSE, the endpoint may be different (e.g. /sse vs /mcp)
        if not sse_url.endswith("/sse"):
            sse_url = self.url + "/sse" if not self.url.endswith("/mcp") else self.url.replace("/mcp", "/sse")
        try:
            if self._use_aiohttp:
                import aiohttp
                assert isinstance(self._session, aiohttp.ClientSession)
                async with self._session.get(sse_url, allow_redirects=False) as resp:
                    async for line in resp.content:
                        decoded = line.decode("utf-8", errors="replace").strip()
                        if decoded.startswith("data: "):
                            data_str = decoded[6:]
                            if data_str:
                                try:
                                    msg = json.loads(data_str)
                                    await self._incoming.put(msg)
                                except json.JSONDecodeError:
                                    pass
            else:
                import httpx
                assert isinstance(self._session, httpx.AsyncClient)
                async with self._session.stream("GET", sse_url) as resp:
                    async for line in resp.aiter_lines():
                        line = line.strip()
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str:
                                try:
                                    msg = json.loads(data_str)
                                    await self._incoming.put(msg)
                                except json.JSONDecodeError:
                                    pass
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.debug("SSE stream error [%s]: %s", self.name, exc)
        finally:
            await self._incoming.put(None)

    async def send(self, message: dict) -> None:
        if not self._connected or self._session is None:
            raise ConnectionError("SSETransport not connected")
        payload = json.dumps(message)
        post_url = self.url
        if hasattr(self._session, "post"):
            try:
                import aiohttp
                if isinstance(self._session, aiohttp.ClientSession):
                    async with self._session.post(
                        post_url,
                        data=payload,
                        content_type="application/json",
                        allow_redirects=False,
                    ) as resp:
                        body = await resp.text()
                        if body.strip():
                            try:
                                msg = json.loads(body)
                                await self._incoming.put(msg)
                            except json.JSONDecodeError:
                                pass
                        return
            except ImportError:
                pass
            import httpx
            if isinstance(self._session, httpx.AsyncClient):
                resp = await self._session.post(post_url, content=payload)
                body = resp.text
                if body.strip():
                    try:
                        msg = json.loads(body)
                        await self._incoming.put(msg)
                    except json.JSONDecodeError:
                        pass
                return
        raise RuntimeError("No HTTP client available")

    async def receive(self) -> Optional[dict]:
        try:
            return await asyncio.wait_for(self._incoming.get(), timeout=self.timeout)
        except asyncio.TimeoutError:
            return None

    async def close(self) -> None:
        self._connected = False
        if self._event_stream_task and not self._event_stream_task.done():
            self._event_stream_task.cancel()
            try:
                await self._event_stream_task
            except asyncio.CancelledError:
                pass
        if self._session and hasattr(self._session, "close"):
            await self._session.close()
        self._session = None
        # Drain queue
        while not self._incoming.empty():
            try:
                self._incoming.get_nowait()
            except asyncio.QueueEmpty:
                break


# ---------------------------------------------------------------------------
# MCPServerConfig
# ---------------------------------------------------------------------------

DANGEROUS_ENV_VARS = frozenset({
    "PATH", "HOME", "USER", "SHELL", "LANG", "LC_ALL", "TMPDIR",
    "DISPLAY", "SSH_AUTH_SOCK", "TERM", "PWD", "OLDPWD", "LOGNAME",
    "XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS",
})

EXPLICIT_CREDENTIAL_ENV_KEYS = frozenset({
    "AMQP_URL", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",
    "AWS_SECURITY_TOKEN", "AWS_SESSION_TOKEN", "AZURE_CLIENT_ID",
    "AZURE_CLIENT_SECRET", "DATABASE_URL", "GH_TOKEN", "GITHUB_TOKEN",
    "GITLAB_TOKEN", "MONGODB_URI", "NODE_AUTH_TOKEN", "NPM_TOKEN",
    "REDIS_URL", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
})


@dataclass
class MCPServerSecurityPolicy:
    """Security policy for a single MCP server connection."""

    # Tool-level allowlist / denylist (empty means unrestricted)
    tool_allowlist: list[str] = field(default_factory=list)
    tool_denylist: list[str] = field(default_factory=list)

    # Env var filtering: drop dangerous inherited host vars
    filter_dangerous_env: bool = True

    # Maximum concurrent tool calls
    max_concurrent_calls: int = 10

    # Timeout per tool call (seconds)
    call_timeout: float = 120.0

    # Whether to allow network access from the subprocess (stdio only)
    allow_network: bool = True

    def is_tool_allowed(self, tool_name: str) -> bool:
        if self.tool_denylist and tool_name in self.tool_denylist:
            return False
        if self.tool_allowlist and tool_name not in self.tool_allowlist:
            return False
        return True

    @staticmethod
    def filter_env(env: dict[str, str]) -> dict[str, str]:
        """Drop dangerous inherited env vars before spawning subprocesses."""
        safe: dict[str, str] = {}
        for key, value in env.items():
            upper = key.upper()
            # Always allow explicit credential keys
            if upper in EXPLICIT_CREDENTIAL_ENV_KEYS:
                safe[key] = value
                continue
            # Drop dangerous host-inherited vars
            if key in DANGEROUS_ENV_VARS:
                continue
            # Drop vars that look like inherited host config pivots
            if upper.startswith(("HOSTNAME", "SSH_", "DISPLAY")):
                continue
            safe[key] = value
        return safe


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server."""

    # Server identity
    name: str

    # Stdio transport fields
    command: str = ""
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    cwd: str | None = None

    # HTTP / SSE transport fields
    url: str = ""
    headers: dict[str, str] = field(default_factory=dict)

    # Transport type: "stdio", "http", "sse"
    transport_type: str = "stdio"

    # Capability negotiation
    supported_capabilities: list[str] = field(default_factory=lambda: ["tools"])
    requested_tools_capability: bool = True

    # Connection tuning
    connection_timeout: float = 30.0
    request_timeout: float = 120.0
    supports_parallel_tool_calls: bool = True

    # Security
    security: MCPServerSecurityPolicy = field(default_factory=MCPServerSecurityPolicy)

    def resolve_transport(self) -> MCPTransport:
        """Factory: build the right transport from this config."""
        env = MCPServerSecurityPolicy.filter_env(self.env) if self.security.filter_dangerous_env else self.env
        if self.transport_type == "stdio":
            return StdioTransport(
                command=self.command,
                args=self.args,
                env=env,
                cwd=self.cwd,
                name=self.name,
            )
        elif self.transport_type == "http":
            return HTTPTransport(
                url=self.url,
                headers=self.headers,
                name=self.name,
                timeout=self.connection_timeout,
            )
        elif self.transport_type == "sse":
            return SSETransport(
                url=self.url,
                headers=self.headers,
                name=self.name,
                timeout=self.connection_timeout,
            )
        else:
            raise ValueError(f"Unknown transport type: {self.transport_type}")


# ---------------------------------------------------------------------------
# MCPServer — host an MCP server
# ---------------------------------------------------------------------------

@dataclass
class MCPTool:
    """Registered tool with its schema."""

    name: str
    description: str = ""
    input_schema: dict = field(default_factory=dict)
    handler: Callable[..., Any] | None = None


class MCPServer:
    """
    MCP server that hosts tools and handles JSON-RPC 2.0 requests.

    Usage:
        server = MCPServer(name="my-server")
        server.register_tool("greet", "Say hello", {"type": "object", "properties": {"name": {"type": "string"}}}, greet_handler)
        await server.run_stdio()
    """

    SERVER_VERSION = "1.0.0"

    def __init__(self, name: str = "hellochusquis-mcp", version: str | None = None):
        self.name = name
        self.version = version or self.SERVER_VERSION
        self._tools: dict[str, MCPTool] = {}
        self._running = False
        self._transport: MCPTransport | None = None

    def register_tool(
        self,
        name: str,
        description: str = "",
        input_schema: dict | None = None,
        handler: Callable[..., Any] | None = None,
    ) -> None:
        """Register a tool that will be exposed via MCP."""
        self._tools[name] = MCPTool(
            name=name,
            description=description,
            input_schema=input_schema or {"type": "object", "properties": {}},
            handler=handler,
        )

    def unregister_tool(self, name: str) -> None:
        self._tools.pop(name, None)

    def get_tool(self, name: str) -> MCPTool | None:
        return self._tools.get(name)

    def list_tool_schemas(self) -> list[dict]:
        """Return tool schemas in MCP tools/list format."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "inputSchema": t.input_schema,
            }
            for t in self._tools.values()
        ]

    def capabilities(self) -> dict:
        caps: dict[str, Any] = {}
        if self._tools:
            caps["tools"] = {"listChanged": False}
        return caps

    async def _handle_request(self, message: dict) -> dict | None:
        """Process one JSON-RPC 2.0 request/notification."""
        method = message.get("method", "")
        params = message.get("params", {})
        req_id = message.get("id")  # None for notifications

        try:
            if method == "initialize":
                return self._handle_initialize(req_id, params)
            elif method == "initialized":
                # Client ack — no response
                return None
            elif method == "notifications/initialized":
                return None
            elif method == "tools/list":
                return self._handle_list_tools(req_id)
            elif method == "tools/call":
                return await self._handle_call_tool(req_id, params)
            elif method == "ping":
                return jsonrpc_response(req_id, {})
            elif method == "shutdown":
                self._running = False
                return jsonrpc_response(req_id, None)
            elif method == "notifications/cancelled":
                return None  # notification, no response
            elif req_id is not None:
                return jsonrpc_error_response(req_id, MethodNotFound(method))
            else:
                # Unknown notification — silently ignore
                return None
        except JSONRPCError as exc:
            if req_id is not None:
                return jsonrpc_error_response(req_id, exc)
            return None
        except Exception as exc:
            if req_id is not None:
                return jsonrpc_error_response(req_id, InternalError(str(exc)))
            return None

    def _handle_initialize(self, req_id: Any, params: dict) -> dict:
        server_info = {"name": self.name, "version": self.version}
        capabilities = self.capabilities()
        result = {
            "protocolVersion": "2024-11-05",
            "serverInfo": server_info,
            "capabilities": capabilities,
        }
        return jsonrpc_response(req_id, result)

    def _handle_list_tools(self, req_id: Any) -> dict:
        tools = self.list_tool_schemas()
        return jsonrpc_response(req_id, {"tools": tools})

    async def _handle_call_tool(self, req_id: Any, params: dict) -> dict:
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        tool = self._tools.get(tool_name)
        if not tool:
            return jsonrpc_error_response(
                req_id, InvalidParams(f"Unknown tool: {tool_name}")
            )
        if tool.handler is None:
            return jsonrpc_error_response(
                req_id, InvalidParams(f"Tool has no handler: {tool_name}")
            )
        try:
            result = await self._invoke_handler(tool, arguments)
            # Normalize result to MCP content format
            content = self._to_content_blocks(result)
            return jsonrpc_response(req_id, {"content": content, "isError": False})
        except Exception as exc:
            content = self._to_content_blocks(f"Tool error: {exc}")
            return jsonrpc_response(req_id, {"content": content, "isError": True})

    async def _invoke_handler(self, tool: MCPTool, arguments: dict) -> Any:
        """Invoke tool handler, supporting both sync and async."""
        result = tool.handler(**arguments)
        if asyncio.iscoroutine(result):
            return await result
        return result

    def _to_content_blocks(self, result: Any) -> list[dict]:
        """Convert tool result to MCP content blocks."""
        if isinstance(result, list):
            blocks = []
            for item in result:
                if isinstance(item, dict) and "type" in item:
                    blocks.append(item)
                else:
                    blocks.append({"type": "text", "text": str(item)})
            return blocks
        if isinstance(result, dict):
            if "type" in result:
                return [result]
            # Try to extract content field
            if "content" in result:
                raw = result["content"]
                if isinstance(raw, list):
                    return [b if isinstance(b, dict) and "type" in b else {"type": "text", "text": str(b)} for b in raw]
                return [{"type": "text", "text": str(raw)}]
            return [{"type": "text", "text": json.dumps(result)}]
        return [{"type": "text", "text": str(result) if result is not None else ""}]

    # ---- Run modes ----

    async def run_stdio(self) -> None:
        """Run the server reading/writing JSON-RPC on stdin/stdout."""
        self._running = True
        loop = asyncio.get_event_loop()
        while self._running:
            try:
                line = await loop.run_in_executor(None, sys.stdin.readline)
            except EOFError:
                break
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                resp = jsonrpc_error_response(None, ParseError())
                self._write_line(resp)
                continue
            response = await self._handle_request(message)
            if response is not None:
                self._write_line(response)
        await self._cleanup()

    async def run_with_transport(self, transport: MCPTransport) -> None:
        """Run the server over any transport."""
        self._transport = transport
        self._running = True
        async with transport:
            while self._running:
                message = await transport.receive()
                if message is None:
                    break
                response = await self._handle_request(message)
                if response is not None:
                    await transport.send(response)
        await self._cleanup()

    def _write_line(self, obj: dict) -> None:
        """Write a JSON-RPC message to stdout (stdio mode)."""
        payload = json.dumps(obj) + "\n"
        sys.stdout.write(payload)
        sys.stdout.flush()

    async def _cleanup(self) -> None:
        self._running = False
        if self._transport:
            await self._transport.close()


# ---------------------------------------------------------------------------
# MCPClient — connect to multiple MCP servers
# ---------------------------------------------------------------------------

@dataclass
class MCPServerConnection:
    """State for a connected MCP server."""

    name: str
    config: MCPServerConfig
    transport: MCPTransport
    tools: list[dict] = field(default_factory=list)
    connected: bool = False
    server_info: dict = field(default_factory=dict)
    capabilities: dict = field(default_factory=dict)
    last_heartbeat: float = 0.0


class MCPClient:
    """
    Connect to multiple MCP servers simultaneously.

    - Auto-discovers tools from each connected server.
    - Routes tool calls to the correct server.
    - Tool name namespacing: server__tool.
    - Connection health checks.
    """

    def __init__(self):
        self._connections: dict[str, MCPServerConnection] = {}
        self._tool_map: dict[str, str] = {}  # namespaced_name → server_name
        self._raw_tool_map: dict[str, str] = {}  # raw tool_name → server_name (for non-namespaced lookup)
        self._connected = False
        self._health_task: Optional[asyncio.Task[None]] = None

    @property
    def is_connected(self) -> bool:
        return self._connected

    # -- Backward-compatible property: old code used self.mcp_client.servers --
    @property
    def servers(self) -> dict[str, MCPServerConfig]:
        """Return server configs keyed by name (backward compat with old interface)."""
        return {name: conn.config for name, conn in self._connections.items()}

    def add_server(self, name: str, config: MCPServerConfig) -> None:
        """Register an MCP server config before connecting."""
        if name in self._connections:
            raise ValueError(f"Server '{name}' already registered")
        transport = config.resolve_transport()
        self._connections[name] = MCPServerConnection(
            name=name, config=config, transport=transport
        )

    def add_server_direct(self, name: str, transport: MCPTransport) -> None:
        """Register a server with a pre-built transport."""
        if name in self._connections:
            raise ValueError(f"Server '{name}' already registered")
        self._connections[name] = MCPServerConnection(
            name=name,
            config=MCPServerConfig(name=name, transport_type=transport.transport_type),
            transport=transport,
        )

    async def connect(self, name: str | None = None) -> dict:
        """
        Connect to a specific server or all servers.

        Returns a summary dict with connection results.
        """
        results: dict[str, dict] = {}
        targets = [name] if name else list(self._connections.keys())

        for server_name in targets:
            conn = self._connections.get(server_name)
            if not conn:
                results[server_name] = {"success": False, "error": f"Server not found: {server_name}"}
                continue
            if conn.connected:
                results[server_name] = {"success": True, "server": server_name, "status": "already connected"}
                continue
            try:
                await conn.transport.connect()
                # Send initialize
                init_request = jsonrpc_request(
                    "initialize",
                    {
                        "protocolVersion": "2024-11-05",
                        "clientInfo": {"name": "hellochusquis-mcp-client", "version": "1.0.0"},
                        "capabilities": {},
                    },
                    req_id=1,
                )
                await conn.transport.send(init_request)
                init_response = await conn.transport.receive()
                if init_response and "result" in init_response:
                    conn.server_info = init_response["result"].get("serverInfo", {})
                    conn.capabilities = init_response["result"].get("capabilities", {})
                # Send initialized notification
                await conn.transport.send(jsonrpc_notification("notifications/initialized"))
                # Discover tools
                tools = await self._discover_tools(conn)
                conn.tools = tools
                conn.connected = True
                conn.last_heartbeat = time.time()
                results[server_name] = {
                    "success": True,
                    "server": server_name,
                    "tools_count": len(tools),
                }
            except Exception as exc:
                results[server_name] = {"success": False, "error": str(exc)}

        if name is None:
            self._connected = any(c.connected for c in self._connections.values())
        return results

    async def _discover_tools(self, conn: MCPServerConnection) -> list[dict]:
        """Send tools/list and index discovered tools."""
        req_id = int(time.time() * 1000) % 1_000_000
        request = jsonrpc_request("tools/list", {}, req_id)
        await conn.transport.send(request)
        response = await conn.transport.receive()
        if response and "result" in response:
            tools = response["result"].get("tools", [])
        else:
            tools = []
        # Index tools with namespacing
        for tool in tools:
            raw_name = tool.get("name", "")
            namespaced = f"{conn.name}__{raw_name}"
            self._tool_map[namespaced] = conn.name
            self._raw_tool_map[raw_name] = conn.name
        return tools

    def list_tools(self, server: str | None = None) -> list[dict]:
        """List all discovered tools, optionally filtered by server name."""
        tools = []
        for conn in self._connections.values():
            if not conn.connected:
                continue
            if server and conn.name != server:
                continue
            for tool in conn.tools:
                tools.append({
                    "server": conn.name,
                    "name": tool.get("name", ""),
                    "namespaced_name": f"{conn.name}__{tool.get('name', '')}",
                    "description": tool.get("description", ""),
                    "inputSchema": tool.get("inputSchema", {}),
                })
        return tools

    async def call_tool(
        self,
        tool_name_or_server: str,
        arguments_or_tool: dict | str | None = None,
        arguments: dict | None = None,
        timeout: float | None = None,
        # Support old positional call: call_tool(server, tool_name, arguments)
        **kwargs: Any,
    ) -> dict:
        """
        Call a tool by name. Routes to the correct server.

        Supports two call signatures:
          - NEW: call_tool(tool_name, arguments=..., server=...)
          - OLD (backward compat): call_tool(server, tool_name, arguments)

        tool_name can be:
        - namespaced: "server__tool"
        - raw: "tool" (uses raw_tool_map, picks first match)
        - explicit server param overrides routing
        """
        # --- Detect old call signature: first arg is server, second is tool name ---
        if arguments_or_tool is not None and isinstance(arguments_or_tool, str):
            # OLD signature: call_tool(server, tool_name, arguments)
            server_name = tool_name_or_server
            tool_name = arguments_or_tool
            if arguments is None:
                arguments = kwargs.get("arguments", {})
        else:
            # NEW signature: call_tool(tool_name, arguments=..., server=...)
            tool_name = tool_name_or_server
            arguments = arguments_or_tool if isinstance(arguments_or_tool, dict) else (arguments or {})
            server_name = kwargs.get("server", None)

        arguments = arguments or {}
        # Resolve server
        if server_name is None:
            server_name = self._tool_map.get(tool_name) or self._raw_tool_map.get(tool_name)
        if not server_name:
            return {"success": False, "error": f"No server found for tool: {tool_name}"}

        conn = self._connections.get(server_name)
        if not conn or not conn.connected:
            return {"success": False, "error": f"Server not connected: {server_name}"}

        # Strip namespace prefix for the actual MCP call
        raw_tool_name = tool_name
        if tool_name.startswith(f"{server_name}__"):
            raw_tool_name = tool_name[len(server_name) + 2:]

        # Check security policy
        if not conn.config.security.is_tool_allowed(raw_tool_name):
            return {"success": False, "error": f"Tool denied by security policy: {raw_tool_name}"}

        # Check tool exists on server
        tool_exists = any(t.get("name") == raw_tool_name for t in conn.tools)
        if not tool_exists:
            return {"success": False, "error": f"Tool not found on server {server_name}: {raw_tool_name}"}

        req_id = int(time.time() * 1_000_000) % 1_000_000_000
        call_timeout = timeout or conn.config.security.call_timeout

        try:
            request = jsonrpc_request(
                "tools/call",
                {"name": raw_tool_name, "arguments": arguments},
                req_id,
            )
            await asyncio.wait_for(conn.transport.send(request), timeout=call_timeout)
            response = await asyncio.wait_for(conn.transport.receive(), timeout=call_timeout)

            if response is None:
                return {"success": False, "error": "No response from server"}

            if "error" in response:
                err = response["error"]
                return {
                    "success": False,
                    "error": err.get("message", "Tool call failed"),
                    "code": err.get("code"),
                    "data": err.get("data"),
                }

            result = response.get("result", {})
            return {"success": True, "data": result, "server": server_name}

        except asyncio.TimeoutError:
            return {"success": False, "error": f"Tool call timed out after {call_timeout}s"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def health_check(self) -> dict[str, dict]:
        """Check health of all connections. Returns per-server status."""
        results: dict[str, dict] = {}
        for name, conn in self._connections.items():
            if not conn.connected:
                results[name] = {"healthy": False, "reason": "not connected"}
                continue
            try:
                req_id = int(time.time() * 1000) % 1_000_000
                ping = jsonrpc_request("ping", {}, req_id)
                await asyncio.wait_for(conn.transport.send(ping), timeout=5.0)
                resp = await asyncio.wait_for(conn.transport.receive(), timeout=5.0)
                if resp and "result" in resp:
                    conn.last_heartbeat = time.time()
                    results[name] = {"healthy": True, "latency_ms": 0}
                else:
                    results[name] = {"healthy": False, "reason": "invalid ping response"}
            except Exception as exc:
                results[name] = {"healthy": False, "reason": str(exc)}
        return results

    async def disconnect(self, name: str | None = None) -> None:
        """Disconnect from specific or all servers."""
        targets = [name] if name else list(self._connections.keys())
        for server_name in targets:
            conn = self._connections.get(server_name)
            if not conn:
                continue
            try:
                # Send shutdown
                if conn.connected and conn.transport.is_connected:
                    shutdown = jsonrpc_request("shutdown", None, 999999)
                    await asyncio.wait_for(conn.transport.send(shutdown), timeout=3.0)
            except Exception:
                pass
            await conn.transport.close()
            conn.connected = False
            # Remove from tool maps
            for ns_name, s_name in list(self._tool_map.items()):
                if s_name == server_name:
                    del self._tool_map[ns_name]
            for raw_name, s_name in list(self._raw_tool_map.items()):
                if s_name == server_name:
                    del self._raw_tool_map[raw_name]

        if name is None:
            self._connections.clear()
            self._tool_map.clear()
            self._raw_tool_map.clear()
            self._connected = False
            if self._health_task and not self._health_task.done():
                self._health_task.cancel()

    async def start_health_monitor(self, interval: float = 30.0) -> None:
        """Background health check loop."""
        if self._health_task and not self._health_task.done():
            return
        self._health_task = asyncio.create_task(self._health_loop(interval))

    async def _health_loop(self, interval: float) -> None:
        try:
            while True:
                await asyncio.sleep(interval)
                results = await self.health_check()
                for name, status in results.items():
                    if not status.get("healthy"):
                        logger.warning("MCP server %s unhealthy: %s", name, status.get("reason"))
        except asyncio.CancelledError:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        asyncio.get_event_loop().run_until_complete(self.disconnect())

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.disconnect()


# ---------------------------------------------------------------------------
# MCPToolBridge — bridge MCP tools ↔ HelloChusquis agent tools
# ---------------------------------------------------------------------------

@dataclass
class AgentTool:
    """HelloChusquis agent tool schema (what the agent runtime expects)."""

    name: str
    description: str = ""
    parameters: dict = field(default_factory=dict)  # JSON Schema for input
    handler: Callable[..., Any] | None = None


class MCPToolBridge:
    """
    Bridge between MCP tools and HelloChusquis agent tools.

    - Converts MCP tool schemas to agent tool schemas.
    - Routes agent tool calls through MCP protocol.
    - Manages the lifecycle of bridged connections.
    """

    def __init__(self, client: MCPClient | None = None):
        self._client = client or MCPClient()
        self._bridged_tools: dict[str, MCPToolBridgeEntry] = {}

    @property
    def client(self) -> MCPClient:
        return self._client

    def register_server(self, name: str, config: MCPServerConfig) -> None:
        """Register an MCP server to bridge tools from."""
        self._client.add_server(name, config)

    def register_server_transport(self, name: str, transport: MCPTransport) -> None:
        self._client.add_server_direct(name, transport)

    async def connect_all(self) -> dict:
        """Connect to all registered MCP servers and discover tools."""
        return await self._client.connect()

    def get_agent_tools(self, server: str | None = None) -> list[AgentTool]:
        """
        Get all discovered MCP tools converted to agent tool format.

        This is what the HelloChusquis agent runtime consumes.
        """
        mcp_tools = self._client.list_tools(server=server)
        agent_tools = []
        for tool in mcp_tools:
            ns_name = tool["namespaced_name"]
            agent_tool = self._convert_mcp_to_agent(tool)
            self._bridged_tools[ns_name] = MCPToolBridgeEntry(
                mcp_tool=tool,
                agent_tool=agent_tool,
                server_name=tool["server"],
                raw_tool_name=tool["name"],
            )
            agent_tools.append(agent_tool)
        return agent_tools

    def get_agent_tool(self, namespaced_name: str) -> AgentTool | None:
        """Get a single converted agent tool by namespaced name."""
        entry = self._bridged_tools.get(namespaced_name)
        if entry:
            return entry.agent_tool
        # Try to find it
        mcp_tools = self._client.list_tools()
        for tool in mcp_tools:
            if tool["namespaced_name"] == namespaced_name:
                agent_tool = self._convert_mcp_to_agent(tool)
                self._bridged_tools[namespaced_name] = MCPToolBridgeEntry(
                    mcp_tool=tool,
                    agent_tool=agent_tool,
                    server_name=tool["server"],
                    raw_tool_name=tool["name"],
                )
                return agent_tool
        return None

    async def call_agent_tool(self, namespaced_name: str, arguments: dict) -> dict:
        """
        Call a tool through the bridge. Routes via MCP protocol.

        Returns the tool result in agent-consumable format.
        """
        entry = self._bridged_tools.get(namespaced_name)
        if not entry:
            return {"success": False, "error": f"Bridged tool not found: {namespaced_name}"}

        # Validate input against schema
        schema = entry.mcp_tool.get("inputSchema", {})
        validation_error = self._validate_input(schema, arguments)
        if validation_error:
            return {"success": False, "error": f"Input validation failed: {validation_error}"}

        # Route through MCP client
        result = await self._client.call_tool(
            namespaced_name,
            arguments=arguments,
            server=entry.server_name,
        )

        if not result.get("success"):
            return result

        # Convert MCP result to agent tool result format
        mcp_result = result.get("data", {})
        return self._convert_mcp_result_to_agent(mcp_result)

    def _convert_mcp_to_agent(self, mcp_tool: dict) -> AgentTool:
        """Convert MCP tool schema to agent tool schema."""
        input_schema = mcp_tool.get("inputSchema", {})
        # MCP uses inputSchema (JSON Schema), agent tools use parameters (JSON Schema)
        # They're compatible, just map them
        return AgentTool(
            name=mcp_tool.get("namespaced_name", mcp_tool.get("name", "")),
            description=mcp_tool.get("description", ""),
            parameters=input_schema,
            handler=None,  # Calls go through the bridge, not direct handlers
        )

    def _convert_mcp_result_to_agent(self, mcp_result: dict) -> dict:
        """Convert MCP tool call result to agent tool result format."""
        content = mcp_result.get("content", [])
        is_error = mcp_result.get("isError", False)

        if isinstance(content, list):
            texts = []
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        texts.append(block.get("text", ""))
                    else:
                        texts.append(json.dumps(block))
                else:
                    texts.append(str(block))
            result_text = "\n".join(texts)
        else:
            result_text = str(content)

        if is_error:
            return {"success": False, "error": result_text}
        return {"success": True, "data": result_text}

    def _validate_input(self, schema: dict, arguments: dict) -> str | None:
        """
        Basic JSON Schema validation.

        Returns error message if validation fails, None if OK.
        """
        if not schema or schema.get("type") != "object":
            return None  # No schema or non-object schema → skip validation

        properties = schema.get("properties", {})
        required = schema.get("required", [])

        # Check required fields
        for field_name in required:
            if field_name not in arguments:
                return f"Missing required field: {field_name}"

        # Check type of provided fields (basic check)
        for field_name, value in arguments.items():
            if field_name in properties:
                expected_type = properties[field_name].get("type")
                if expected_type:
                    actual_type = type(value).__name__
                    type_map = {
                        "str": "string", "int": "integer", "float": "number",
                        "bool": "boolean", "list": "array", "dict": "object",
                    }
                    actual_mcp_type = type_map.get(actual_type, actual_type)
                    if actual_mcp_type != expected_type:
                        # Allow int/number coercion
                        if expected_type == "number" and actual_type in ("int", "float"):
                            continue
                        return f"Field '{field_name}': expected {expected_type}, got {actual_mcp_type}"

        return None

    def summary(self) -> dict:
        """Return a summary of all bridged tools."""
        return {
            "servers": {
                name: {
                    "connected": conn.connected,
                    "tools_count": len(conn.tools),
                    "tool_names": [t.get("name", "") for t in conn.tools],
                }
                for name, conn in self._client._connections.items()
            },
            "bridged_tools": list(self._bridged_tools.keys()),
            "total_bridged": len(self._bridged_tools),
        }


@dataclass
class MCPToolBridgeEntry:
    """Internal record for a bridged tool."""

    mcp_tool: dict
    agent_tool: AgentTool
    server_name: str
    raw_tool_name: str


# ---------------------------------------------------------------------------
# Default MCP servers (backward compatible with existing config)
# ---------------------------------------------------------------------------

DEFAULT_MCP_SERVERS: dict[str, dict] = {
    "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", ""],
    },
    "git": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-git"],
    },
    "github": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
    },
    "slack": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-slack"],
    },
    "postgres": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-postgres"],
    },
}


def build_default_configs() -> dict[str, MCPServerConfig]:
    """Build MCPServerConfig instances from DEFAULT_MCP_SERVERS."""
    configs: dict[str, MCPServerConfig] = {}
    for name, cfg in DEFAULT_MCP_SERVERS.items():
        args = list(cfg.get("args", []))
        if name == "filesystem":
            args[-1] = str(_ensure_default_filesystem_workspace())
        configs[name] = MCPServerConfig(
            name=name,
            command=cfg.get("command", ""),
            args=args,
            transport_type="stdio",
        )
    return configs


# ---------------------------------------------------------------------------
# Convenience singleton (backward compat)
# ---------------------------------------------------------------------------

_client: Optional[MCPClient] = None


def get_client() -> MCPClient:
    """Get or create the global MCPClient singleton."""
    global _client
    if _client is None:
        _client = MCPClient()
    return _client


async def get_bridge() -> MCPToolBridge:
    """Get a bridge backed by the global client, connected to all default servers."""
    bridge = MCPToolBridge(client=get_client())
    # Auto-register default servers
    for name, config in build_default_configs().items():
        try:
            bridge.register_server(name, config)
        except ValueError:
            pass  # Already registered
    return bridge
