"""Shared HTTP auth stack for the api/ and web/ servers.

One implementation of the API-key storage, bearer authentication,
principal helpers and the auth/security-header middleware — the two
servers parameterize it instead of keeping divergent copies.
"""
import os
import secrets
from pathlib import Path

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from core.identity import Permission, Principal, authenticate_bearer, legacy_owner
from core.logger import get_logger

logger = get_logger("http_auth")

# --- Token auth config ---
API_KEY_DIR = Path.home() / ".hellochusquis"
API_KEY_FILE = API_KEY_DIR / "api_key.txt"


def secure_api_key_storage() -> None:
    """Restrict local credential storage to the current operating-system user."""
    API_KEY_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(API_KEY_DIR, 0o700)
    if API_KEY_FILE.exists():
        os.chmod(API_KEY_FILE, 0o600)


def load_or_generate_api_key() -> str:
    """Load or generate a key with owner-only filesystem permissions."""
    if key := os.environ.get("HELLOCHUSQUIS_API_KEY", ""):
        return key
    secure_api_key_storage()
    if API_KEY_FILE.exists():
        existing = API_KEY_FILE.read_text().strip()
        if existing:
            return existing
    key = secrets.token_urlsafe(32)
    try:
        # O_EXCL create: api/ and web/ may boot together; if the other
        # process won the race, use ITS key so both agree.
        with open(API_KEY_FILE, "x") as f:
            f.write(key + "\n")
    except FileExistsError:
        return API_KEY_FILE.read_text().strip()
    os.chmod(API_KEY_FILE, 0o600)
    return key


def authenticate(token: str, required_api_key: str) -> Principal | None:
    """Resolve a bearer token to a principal, or ``None`` when unknown."""
    return authenticate_bearer(token, required_api_key)


def current_principal(
    request, required_api_key: str, auth_enabled: bool = True
) -> Principal:
    """Return the principal attached by the auth middleware.

    With authentication explicitly disabled for local development every caller
    is the owner, matching the pre-identity behaviour of that override.
    """
    principal = getattr(getattr(request, "state", None), "principal", None)
    if principal is None:
        if not auth_enabled:
            return legacy_owner()
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="Authentication required")
    return principal


def require_permission(
    request, permission: Permission, required_api_key: str, auth_enabled: bool = True
) -> Principal:
    """Authorize the caller for one operation, or fail with 403."""
    principal = current_principal(request, required_api_key, auth_enabled)
    if not principal.has(permission):
        logger.warning(
            "Denied %s for %s (role=%s)", permission.value, principal.name, principal.role.value
        )
        from fastapi import HTTPException

        raise HTTPException(
            status_code=403,
            detail=f"Role '{principal.role.value}' is not allowed to perform this operation",
        )
    return principal


class AuthMiddleware(BaseHTTPMiddleware):
    """Bearer-token gate. ``public_get_paths`` are served without a token."""

    def __init__(self, app, required_api_key: str, auth_enabled: bool = True,
                 public_get_paths: tuple = (), public_paths: tuple = ()):
        super().__init__(app)
        self.required_api_key = required_api_key
        self.auth_enabled = auth_enabled
        self.public_get_paths = frozenset(public_get_paths)
        self.public_paths = frozenset(public_paths)

    async def dispatch(self, request, call_next):
        path = request.url.path

        # CORS preflight: pass through OPTIONS (browser sends before actual request)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Explicit local-development override only — enforced by the caller
        # (binding beyond loopback re-enables auth).
        if not self.auth_enabled:
            return await call_next(request)

        if request.method == "GET" and path in self.public_get_paths:
            return await call_next(request)

        # Auth bootstrap endpoints (any method): the frontend needs these
        # without a token, and /auth/verify applies its own rate limiter.
        if path in self.public_paths:
            return await call_next(request)

        # Check Authorization header
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"},
            )
        token = auth_header[7:]  # strip "Bearer "
        principal = authenticate(token, self.required_api_key)
        if principal is None:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid API key"},
            )
        request.state.principal = principal
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add defensive headers to every HTTP response, including auth failures."""

    async def dispatch(self, request, call_next):
        try:
            response = await call_next(request)
        except Exception:
            # Let Starlette's error handler deal with it, but don't swallow as None
            raise
        if response is None:
            return JSONResponse(status_code=500, content={"detail": "Internal server error"})
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), camera=()")
        response.headers.setdefault("Cache-Control", "no-store")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'none'; base-uri 'none'; frame-ancestors 'none'; object-src 'none'",
        )
        return response
