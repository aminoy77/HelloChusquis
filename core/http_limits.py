"""Shared HTTP request-size protections for FastAPI/Starlette applications."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

MAX_REQUEST_BODY_BYTES = 1_048_576
_BODY_METHODS = {"POST", "PUT", "PATCH"}


class RequestBodyLimitMiddleware(BaseHTTPMiddleware):
    """Reject oversized request bodies before downstream parsing or handling."""

    def __init__(self, app: Callable[..., Awaitable[Any]], max_body_bytes: int = MAX_REQUEST_BODY_BYTES, dispatch=None):
        super().__init__(app, dispatch)
        self.max_body_bytes = max_body_bytes

    async def dispatch(self, request: Request, call_next):
        if request.method not in _BODY_METHODS:
            return await call_next(request)
        clen = request.headers.get("content-length")
        if clen is not None:
            try:
                if int(clen) > self.max_body_bytes:
                    return JSONResponse(status_code=413, content={"detail": "Request body too large"})
                if int(clen) < 0:
                    return JSONResponse(status_code=400, content={"detail": "Invalid Content-Length"})
            except ValueError:
                return JSONResponse(status_code=400, content={"detail": "Invalid Content-Length"})

        # For chunked/streamed bodies, let it through and rely on downstream
        # Starlette/FastAPI to enforce limits during parsing.
        return await call_next(request)
