import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, field_validator
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.responses import StreamingResponse
import uvicorn
import json
import re
import secrets
from pathlib import Path
from typing import Literal

from core.identity import Permission, Principal, authenticate_bearer, legacy_owner
from core.provider import validate_provider_base_url
from core.runtime import AgentNotReadyError, AgentRuntime
from core.version import __version__
import core.db_memory as db_memory
from core.http_limits import RequestBodyLimitMiddleware
from core.learning import load_learnings, add_feedback
from core.rate_limiter import RateLimiter
from core.logger import get_logger

logger = get_logger("web")

# --- Token auth config ---
_AUTH_DIR = Path.home() / ".hellochusquis"
_AUTH_KEY_FILE = _AUTH_DIR / "api_key.txt"


def _secure_api_key_storage() -> None:
    """Restrict local credential storage to the current operating-system user."""
    _AUTH_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(_AUTH_DIR, 0o700)
    if _AUTH_KEY_FILE.exists():
        os.chmod(_AUTH_KEY_FILE, 0o600)


def _load_or_create_api_key() -> str:
    """Load or generate a key with owner-only filesystem permissions."""
    env_key = os.environ.get("HELLOCHUSQUIS_API_KEY", "")
    if env_key:
        return env_key
    _secure_api_key_storage()
    if _AUTH_KEY_FILE.exists():
        existing = _AUTH_KEY_FILE.read_text().strip()
        if existing:
            return existing
    token = secrets.token_urlsafe(32)
    _AUTH_KEY_FILE.write_text(token + "\n")
    os.chmod(_AUTH_KEY_FILE, 0o600)
    return token



REQUIRED_API_KEY = _load_or_create_api_key()
# The web UI can execute shell, file, browser and integration tools. It is
# therefore protected by default, including on localhost. Set
# HELLOCHUSQUIS_AUTH=0 only for an intentionally trusted, isolated local
# development session; never use that override on a shared machine or network.
_auth_setting = os.environ.get("HELLOCHUSQUIS_AUTH", "").strip().lower()
AUTH_ENABLED = _auth_setting not in ("0", "false", "no", "off")


def _auth_hint() -> str:
    """Operator-only hint about where the API key lives."""
    if os.environ.get("HELLOCHUSQUIS_API_KEY"):
        return "Set via the HELLOCHUSQUIS_API_KEY environment variable."
    if _AUTH_KEY_FILE.exists():
        return f"Stored in {_AUTH_KEY_FILE}"
    return f"Generate one by starting the server (saved to {_AUTH_KEY_FILE})"


def _public_auth_hint() -> str:
    """Return a location-free credential hint suitable for unauthenticated clients."""
    if os.environ.get("HELLOCHUSQUIS_API_KEY"):
        return "Configured by the server administrator."
    return "Configured in local HelloChusquis settings."


def authenticate(token: str) -> Principal | None:
    """Resolve a bearer token to a principal, or ``None`` when unknown."""
    return authenticate_bearer(token, REQUIRED_API_KEY)


def current_principal(request: Request) -> Principal:
    """Return the principal attached by the auth middleware.

    With authentication explicitly disabled for local development every caller
    is the owner, matching the pre-identity behaviour of that override.
    """
    principal = getattr(getattr(request, "state", None), "principal", None)
    if principal is None:
        if not AUTH_ENABLED:
            return legacy_owner()
        raise HTTPException(status_code=401, detail="Authentication required")
    return principal


def require_permission(request: Request, permission: Permission) -> Principal:
    """Authorize the caller for one operation, or fail with 403."""
    principal = current_principal(request)
    if not principal.has(permission):
        logger.warning(
            "Denied %s for %s (role=%s)", permission.value, principal.name, principal.role.value
        )
        raise HTTPException(
            status_code=403,
            detail=f"Role '{principal.role.value}' is not allowed to perform this operation",
        )
    return principal


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # CORS preflight: pass through OPTIONS (browser sends before actual request)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Explicit local-development override only.
        if not AUTH_ENABLED:
            return await call_next(request)

        # Skip auth for static/login endpoints
        if request.method == "GET" and path == "/":
            return await call_next(request)

        # Skip auth for health probes
        if path in ("/health/live", "/health/ready", "/health"):
            return await call_next(request)

        # Skip auth for auth bootstrap endpoints (frontend needs these WITHOUT token)
        if path in ("/auth/check", "/auth/verify"):
            return await call_next(request)

        # Check Authorization header
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"},
            )
        token = auth_header[7:]  # strip "Bearer "
        principal = authenticate(token)
        if principal is None:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid API key"},
            )
        request.state.principal = principal
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add defensive headers to every web response, including auth failures."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
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


app = FastAPI()
app.add_middleware(RequestBodyLimitMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
# Keep the web server alive before initial setup; agent-dependent routes return
# a clear 503 until a provider is configured.
runtime = AgentRuntime()


_SESSION_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


def _session_id(request: Request) -> str:
    """Return the explicit session required by stateful HTTP operations."""
    supplied = request.headers.get("x-hellochusquis-session", "").strip()
    if not supplied:
        raise HTTPException(
            status_code=400,
            detail="X-HelloChusquis-Session header is required for stateful operations",
        )
    if not _SESSION_ID_RE.fullmatch(supplied):
        raise HTTPException(status_code=400, detail="Invalid X-HelloChusquis-Session header")
    return supplied


def _require_agent(http_request: Request | None = None):
    try:
        if http_request is None:
            return runtime.get()
        principal = current_principal(http_request)
        # Namespacing the session by principal makes another identity's session
        # id resolve to a new empty session instead of somebody else's context.
        scoped_session_id = f"web:{principal.id}:{_session_id(http_request)}"
        return runtime.get(session_id=scoped_session_id, role=principal.role)
    except AgentNotReadyError as exc:
        logger.warning("Agent runtime requested before ready: %s", exc)
        raise HTTPException(status_code=503, detail="Agent runtime is not ready. Complete setup and retry.") from exc


# Rate limiters: /chat and /models = 30/min, /feedback = 10/min, forced model refresh = 5/min,
# /runtime/reload = 3/min, /update-provider = 15/min, and public key verification = 20/min.
_chat_limiter = RateLimiter(requests_per_minute=30)
_feedback_limiter = RateLimiter(requests_per_minute=10)
_models_limiter = RateLimiter(requests_per_minute=30)
_models_refresh_limiter = RateLimiter(requests_per_minute=5)
_reload_limiter = RateLimiter(requests_per_minute=3)
_provider_update_limiter = RateLimiter(requests_per_minute=15)
_auth_verify_limiter = RateLimiter(requests_per_minute=20)


def _get_client_ip(request: Request) -> str:
    client = getattr(request, "client", None)
    return client.host if client else "unknown"


def _require_rate_limit(limiter: RateLimiter, request: Request, route: str) -> None:
    """Reject excessive costly or persistent operations from one client."""
    ip = _get_client_ip(request)
    if limiter.is_allowed(ip):
        return
    retry_after = max(1, int(limiter.get_retry_after(ip) + 0.999))
    logger.warning("Rate limit exceeded on %s from %s", route, ip)
    raise HTTPException(
        status_code=429,
        detail="Too many administrative requests",
        headers={"Retry-After": str(retry_after)},
    )


# --- Request models ---

class MessageRequest(BaseModel):
    message: str = Field(max_length=20_000)
    provider: str | None = Field(default=None, max_length=200)
    model: str | None = Field(default=None, max_length=256)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message cannot be empty")
        return value

    @field_validator("provider", "model")
    @classmethod
    def normalize_optional_selector(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class FeedbackRequest(BaseModel):
    type: Literal["positive", "negative"]
    context: str = Field(default="", max_length=500)


class ApprovalDecisionRequest(BaseModel):
    approve: bool


class ConfigRequest(BaseModel):
    data: dict = Field(default_factory=dict)


# --- Routes ---

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the UI with a per-response nonce for its single inline script."""
    nonce = secrets.token_urlsafe(18)
    html_path = Path(__file__).parent / "index.html"
    html = html_path.read_text(encoding="utf-8").replace("<script>", f'<script nonce="{nonce}">', 1)
    csp = (
        "default-src 'self'; "
        f"script-src 'nonce-{nonce}'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; "
        "img-src 'self' data:; connect-src 'self'; base-uri 'none'; "
        "form-action 'self'; frame-ancestors 'none'; object-src 'none'"
    )
    return HTMLResponse(html, headers={"Content-Security-Policy": csp})


@app.get("/auth/check")
def auth_check():
    """Tell the frontend whether auth is required (and where the key lives)."""
    return {
        "auth_required": AUTH_ENABLED,
        "key_hint": _public_auth_hint() if AUTH_ENABLED else "",
    }


@app.post("/auth/verify")
def auth_verify(req: MessageRequest, http_request: Request):
    """Verify a bearer token with a bounded number of public attempts."""
    ip = _get_client_ip(http_request)
    if not _auth_verify_limiter.is_allowed(ip):
        retry_after = max(1, int(_auth_verify_limiter.get_retry_after(ip) + 0.999))
        logger.warning("Rate limit exceeded on /auth/verify from %s", ip)
        raise HTTPException(
            status_code=429,
            detail="Too many verification attempts",
            headers={"Retry-After": str(retry_after)},
        )
    principal = authenticate(req.message)
    if principal is not None:
        return {"status": "ok", "role": principal.role.value, "name": principal.name}
    raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/health")
def health_check():
    providers = runtime.provider_status()
    ready = sum(1 for provider in providers if provider["status"] == "ready")
    return {
        "status": "ok",
        "version": __version__,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "providers": {"total": len(providers), "ready": ready},
        "agent_ready": runtime.is_ready,
    }


@app.get("/health/ready")
def readiness_probe():
    readiness = runtime.readiness()
    if not readiness["ready"]:
        logger.warning("Readiness probe failed: %s", readiness.get("error", "unknown error"))
        raise HTTPException(status_code=503, detail="No providers are ready")
    providers = readiness["providers"]
    ready = sum(1 for provider in providers if provider["status"] == "ready")
    return {"status": "ok", "ready_providers": ready}


@app.get("/health/live")
def liveness_probe():
    return {"status": "ok"}


@app.post("/chat")
def chat(req: MessageRequest, http_request: Request):
    require_permission(http_request, Permission.CHAT)
    ip = http_request.client.host if http_request.client else "unknown"
    if not _chat_limiter.is_allowed(ip):
        retry = _chat_limiter.get_retry_after(ip)
        logger.warning("Rate limit exceeded on /chat from %s", ip)
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Max 30 requests/minute.",
            headers={"Retry-After": str(int(retry) + 1)},
        )

    user_input = req.message.strip()

    # Validate empty
    if not user_input:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Validate length
    if len(req.message) > 20000:
        raise HTTPException(status_code=400, detail="Message too long (max 20000 chars)")

    logger.info("Chat request from %s", ip)
    agent = _require_agent(http_request)

    if user_input == "/clear":
        if not agent.try_acquire_turn():
            raise HTTPException(status_code=409, detail="This conversation is already processing another request")
        try:
            agent.clear_conversation()
            return {"response": "Historial limpiado.", "tool_calls": []}
        finally:
            agent.release_turn()

    if user_input == "/status":
        status = agent.pool.status()
        lines = [f"{'✓' if p['status'] == 'ready' else '✗'} {p['name']} — {p['model']}" for p in status]
        return {"response": "\n".join(lines), "tool_calls": []}

    if not agent.try_acquire_turn():
        raise HTTPException(status_code=409, detail="This conversation is already processing another request")

    tool_calls_log = []

    def record_tool_call(name, args, result):
        tool_calls_log.append({
            "tool": name,
            "args": args,
            "success": result.success,
            "output": result.output[:200],
        })

    try:
        response = agent.run(
            user_input,
            provider=req.provider,
            model=req.model,
            tool_result_callback=record_tool_call,
        )
    except RuntimeError as e:
        logger.error("Chat error: %s", e)
        response = "The request could not be completed. Check server logs."
    finally:
        agent.release_turn()
    return {"response": response, "tool_calls": tool_calls_log}



@app.post("/chat/stream")
def chat_stream(req: MessageRequest, http_request: Request):
    """SSE streaming endpoint. Same contract as /chat but yields chunks."""
    require_permission(http_request, Permission.CHAT)
    ip = http_request.client.host if http_request.client else "unknown"
    if not _chat_limiter.is_allowed(ip):
        retry = _chat_limiter.get_retry_after(ip)
        logger.warning("Rate limit exceeded on /chat/stream from %s", ip)
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Max 30 requests/minute.",
            headers={"Retry-After": str(int(retry) + 1)},
        )

    user_input = req.message.strip()
    if not user_input:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    if len(user_input) > 20000:
        raise HTTPException(status_code=400, detail="Message too long (max 20000 chars)")

    agent = _require_agent(http_request)
    if user_input == "/clear":
        if not agent.try_acquire_turn():
            raise HTTPException(status_code=409, detail="This conversation is already processing another request")
        try:
            agent.clear_conversation()
        finally:
            agent.release_turn()
        text = "Historial limpiado."
        return StreamingResponse(
            iter([f"data: {json.dumps({'type': 'chunk', 'content': text})}\n\n",
                  f"data: {json.dumps({'type': 'done'})}\n\n"]),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    if user_input == "/status":
        status = agent.pool.status()
        text = "\n".join(f"{'OK' if p['status'] == 'ready' else 'FAIL'} {p['name']} - {p['model']}" for p in status)
        return StreamingResponse(
            iter([f"data: {json.dumps({'type': 'chunk', 'content': text})}\n\n",
                  f"data: {json.dumps({'type': 'done'})}\n\n"]),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    if not agent.try_acquire_turn():
        raise HTTPException(status_code=409, detail="This conversation is already processing another request")

    def event_gen():
        try:
            for ev in agent.stream_run(user_input, provider=req.provider, model=req.model):
                payload = json.dumps(ev, ensure_ascii=False)
                yield f"data: {payload}\n\n"
        except RuntimeError:
            logger.warning("Stream execution failed")
            yield f"data: {json.dumps({'type': 'error', 'content': 'Stream failed. Check server logs.'})}\n\n"
        except Exception:
            logger.exception("Stream failed")
            yield f"data: {json.dumps({'type': 'error', 'content': 'Stream failed. Check server logs.'})}\n\n"
        finally:
            agent.release_turn()

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/feedback")
def feedback(req: FeedbackRequest, http_request: Request):
    """Accept bounded feedback from authenticated frontend clients."""
    require_permission(http_request, Permission.CHAT)
    _require_rate_limit(_feedback_limiter, http_request, "/feedback")
    add_feedback(req.type, req.context)
    return {"status": "ok"}


@app.post("/clear")
def clear_history(http_request: Request):
    """Clear the requesting session's in-memory and persistent history."""
    require_permission(http_request, Permission.CHAT)
    agent = _require_agent(http_request)
    if not agent.try_acquire_turn():
        raise HTTPException(status_code=409, detail="This conversation is already processing another request")
    try:
        result = agent.clear_conversation()
        return {"status": "ok", "message": "History cleared", **result}
    finally:
        agent.release_turn()


@app.get("/approvals")
def list_approvals(http_request: Request):
    """List pending high-impact actions for the authenticated client session."""
    require_permission(http_request, Permission.READ_STATE)
    return {"approvals": _require_agent(http_request).pending_approvals()}


@app.get("/audit")
def get_audit_events(http_request: Request, limit: int = 100):
    """Return redacted approval events for the requesting session only."""
    require_permission(http_request, Permission.READ_STATE)
    return {"events": _require_agent(http_request).audit_events(limit=limit)}


@app.post("/approvals/{request_id}")
def decide_approval(
    request_id: str,
    decision: ApprovalDecisionRequest,
    http_request: Request,
):
    """Approve or reject one pending action and execute only after approval."""
    require_permission(http_request, Permission.APPROVE)
    agent = _require_agent(http_request)
    if not agent.try_acquire_turn():
        raise HTTPException(status_code=409, detail="This conversation is already processing another request")
    try:
        approval = agent.decide_approval(request_id, decision.approve)
        if not decision.approve:
            return {"approval": approval, "executed": False}
        result = agent.execute_approved(request_id)
        return {
            "approval": {**approval, "status": "executed"},
            "executed": True,
            "result": {
                "success": result.success,
                "output": result.output,
                "error": result.error,
            },
        }
    except KeyError as exc:
        logger.warning("Approval request not found: %s", exc)
        raise HTTPException(status_code=404, detail="Approval request not found") from exc
    except ValueError as exc:
        logger.warning("Approval request cannot be completed: %s", exc)
        raise HTTPException(status_code=409, detail="Approval request cannot be completed") from exc
    finally:
        agent.release_turn()


@app.post("/runtime/reload")
def reload_runtime(http_request: Request):
    """Reload provider configuration and clear cached HTTP sessions."""
    require_permission(http_request, Permission.MANAGE_RUNTIME)
    _require_rate_limit(_reload_limiter, http_request, "/runtime/reload")
    cleared_sessions = runtime.session_count
    if not runtime.refresh():
        logger.error("Runtime reload failed: %s", runtime.error or "unknown error")
        raise HTTPException(status_code=503, detail="Runtime reload failed")
    return {
        "status": "ok",
        "agent_ready": runtime.is_ready,
        "sessions_cleared": cleared_sessions,
        "version": __version__,
    }


@app.post("/config")
def update_config(req: ConfigRequest):
    """Compatibility endpoint: configuration is edited by the setup CLI."""
    raise HTTPException(
        status_code=409,
        detail="Use 'hellochusquis config' to edit settings, then POST /runtime/reload.",
    )


@app.get("/status")
def status(http_request: Request):
    if not runtime.is_ready:
        return {
            "agent_ready": False,
            "active_sessions": 0,
            "providers": [],
            "plugins": [],
            "error": runtime.error,
            "auth_enabled": AUTH_ENABLED,
        }
    agent = _require_agent(http_request)
    providers = agent.pool.status()
    plugins = [{"name": plugin["name"]} for plugin in agent.plugins]
    summary = db_memory.load_summary()
    sessions = 0
    try:
        import sqlite3
        from pathlib import Path
        db_path = Path.home() / ".hellochusquis/memory.db"
        if db_path.exists():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sessions")
            sessions = cursor.fetchone()[0]
            conn.close()
    except Exception:
        pass
    learnings = load_learnings()
    return {
        "agent_ready": True,
        "active_sessions": runtime.session_count,
        "providers": providers,
        "plugins": plugins,
        "memory": {
            "summary": summary[:200] if summary else "",
            "sessions": sessions
        },
        "learnings": {
            "patterns": len(learnings.get("tool_patterns", {})),
            "improvements": len(learnings.get("system_prompt_improvements", []))
        },
        "auth_enabled": AUTH_ENABLED,
    }


@app.get("/models")
def models(http_request: Request, provider: str = "", refresh: bool = False):
    """Available models for the requesting session's provider configuration."""
    _require_rate_limit(_models_limiter, http_request, "/models")
    if refresh:
        _require_rate_limit(_models_refresh_limiter, http_request, "/models?refresh=true")
    agent = _require_agent(http_request)
    known_names = {provider_status["name"] for provider_status in agent.pool.status()}
    if provider not in known_names:
        raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found")
    try:
        return {"provider": provider, "models": agent.pool.list_models(provider, refresh=refresh)}
    except Exception:
        logger.exception("models fetch failed")
        raise HTTPException(status_code=500, detail="Failed to fetch models")


class ProviderUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    key: str = Field(default="", max_length=4096)
    base: str = Field(default="", max_length=2048)
    model: str = Field(default="", max_length=256)


@app.post("/update-provider")
def update_provider(data: ProviderUpdate, http_request: Request):
    """Update provider configuration for the requesting in-memory session only."""
    require_permission(http_request, Permission.MANAGE_RUNTIME)
    _require_rate_limit(_provider_update_limiter, http_request, "/update-provider")
    agent = _require_agent(http_request)
    # Validate provider name exists
    known_names = {provider_status["name"] for provider_status in agent.pool.status()}
    if data.name not in known_names:
        raise HTTPException(status_code=404, detail=f"Provider '{data.name}' not found")

    base_url = ""
    if data.base:
        try:
            base_url = validate_provider_base_url(data.base)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not agent.try_acquire_turn():
        raise HTTPException(status_code=409, detail="This conversation is already processing another request")
    try:
        if data.key:
            agent.pool.update_api_key(data.name, data.key)
        if base_url:
            agent.pool.update_base_url(data.name, base_url)
        if data.model:
            agent.pool.update_model(data.name, data.model)
        return {"status": "ok", "provider": data.name, "scope": "session"}
    except Exception:
        logger.exception("update-provider failed")
        raise HTTPException(status_code=500, detail="Failed to update provider")
    finally:
        agent.release_turn()


def start(host: str = "127.0.0.1", port: int = 8000):
    if AUTH_ENABLED:
        logger.info("Auth enabled — API key configured (%s)", _auth_hint())
    else:
        logger.warning("Auth disabled by HELLOCHUSQUIS_AUTH=0; use only in an isolated local development environment")
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    start()
