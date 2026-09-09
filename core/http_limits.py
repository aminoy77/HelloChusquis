"""Shared HTTP request-size protections for FastAPI/Starlette applications."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from starlette.responses import JSONResponse

MAX_REQUEST_BODY_BYTES = 1_048_576
_BODY_METHODS = {"POST", "PUT", "PATCH"}


class RequestBodyLimitMiddleware:
    """Reject oversized request bodies before downstream parsing or handling."""

    def __init__(self, app: Callable[..., Awaitable[Any]], max_body_bytes: int = MAX_REQUEST_BODY_BYTES):
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope: dict[str, Any], receive, send) -> None:
        if scope["type"] != "http" or scope["method"] not in _BODY_METHODS:
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        content_length = headers.get(b"content-length")
        if content_length is not None:
            try:
                declared_size = int(content_length)
            except ValueError:
                await self._send_error(scope, receive, send, 400, "Invalid Content-Length header")
                return
            if declared_size < 0 or declared_size > self.max_body_bytes:
                await self._send_error(scope, receive, send, 413, "Request body too large")
                return

        chunks: list[bytes] = []
        received_size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            if message["type"] != "http.request":
                continue
            chunk = message.get("body", b"")
            received_size += len(chunk)
            if received_size > self.max_body_bytes:
                await self._send_error(scope, receive, send, 413, "Request body too large")
                return
            chunks.append(chunk)
            if not message.get("more_body", False):
                break

        body = b"".join(chunks)
        body_sent = False

        async def replay_body() -> dict[str, Any]:
            nonlocal body_sent
            if body_sent:
                return {"type": "http.disconnect"}
            body_sent = True
            return {"type": "http.request", "body": body, "more_body": False}

        await self.app(scope, replay_body, send)

    @staticmethod
    async def _send_error(scope, receive, send, status_code: int, detail: str) -> None:
        await JSONResponse(status_code=status_code, content={"detail": detail})(scope, receive, send)
