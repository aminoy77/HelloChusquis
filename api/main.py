from datetime import datetime, timezone
from typing import Literal
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import uvicorn
import hmac
import secrets
import os
import json
import re
from pathlib import Path
from core.runtime import AgentNotReadyError, AgentRuntime
from core.rate_limiter import RateLimiter
from core.version import __version__
from core.logger import get_logger

logger = get_logger("api")

# --- Token auth config ---
API_KEY_DIR = Path.home() / ".hellochusquis"
API_KEY_FILE = API_KEY_DIR / "api_key.txt"

def _secure_api_key_storage() -> None:
    """Restrict local credential storage to the current operating-system user."""
    API_KEY_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(API_KEY_DIR, 0o700)
    if API_KEY_FILE.exists():
        os.chmod(API_KEY_FILE, 0o600)


def _load_or_generate_api_key() -> str:
    """Load or generate a key with owner-only filesystem permissions."""
    if key := os.environ.get("HELLOCHUSQUIS_API_KEY", ""):
        return key
    _secure_api_key_storage()
    if API_KEY_FILE.exists():
        return API_KEY_FILE.read_text().strip()
    key = secrets.token_urlsafe(32)
    API_KEY_FILE.write_text(key + "\n")
    os.chmod(API_KEY_FILE, 0o600)
    return key

REQUIRED_API_KEY = _load_or_generate_api_key()
AUTH_ENABLED = True  # Always enabled


def _verify_token(token: str) -> bool:
    """Constant-time token comparison to prevent timing attacks."""
    return hmac.compare_digest(token, REQUIRED_API_KEY)


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # CORS preflight: pass through OPTIONS (browser sends before actual request)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Skip auth for read-only status endpoints
        if request.method == "GET" and request.url.path in (
            "/", "/health", "/health/live", "/health/ready"
        ):
            return await call_next(request)

        # Protect everything else (POST endpoints, /history, /clear)
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"},
            )
        token = auth_header[7:]  # strip "Bearer "
        if not _verify_token(token):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid API key"},
            )
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add defensive headers to every HTTP response, including auth failures."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Cache-Control", "no-store")
        return response


app = FastAPI(title="HelloChusquis API", version=__version__)
app.add_middleware(AuthMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Rate limiters: /chat = 30/min, /feedback = 10/min
_chat_limiter = RateLimiter(requests_per_minute=30)
_feedback_limiter = RateLimiter(requests_per_minute=10)


def _get_client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"

# The API stays live even before first-time setup. Endpoints that need an
# agent return a clear 503 until the user runs `hellochusquis setup`.
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
        session_id = _session_id(http_request) if http_request is not None else None
        return runtime.get(session_id=session_id)
    except AgentNotReadyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


class ChatRequest(BaseModel):
    message: str
    stream: bool = True

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty")
        if len(v) > 20000:
            raise ValueError("Message exceeds maximum length of 20000 characters")
        return v


class FeedbackRequest(BaseModel):
    type: Literal["positive", "negative"]
    context: str = ""


class ApprovalDecisionRequest(BaseModel):
    approve: bool


@app.get("/")
def root():
    return {"name": "HelloChusquis", "version": __version__, "status": "running"}


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
        raise HTTPException(status_code=503, detail=readiness.get("error", "No providers ready"))
    providers = readiness["providers"]
    ready = sum(1 for provider in providers if provider["status"] == "ready")
    return {"status": "ok", "ready_providers": ready}


@app.get("/health/live")
def liveness_probe():
    return {"status": "ok"}


@app.get("/status")
def get_status():
    if not runtime.is_ready:
        return {
            "agent_ready": False,
            "active_sessions": 0,
            "providers": [],
            "plugins": [],
            "error": runtime.error,
        }
    agent = _require_agent()
    return {
        "agent_ready": True,
        "active_sessions": runtime.session_count,
        "providers": agent.pool.status(),
        "plugins": [plugin["name"] for plugin in agent.plugins],
        "memory": {"sessions": "N/A", "summary": "Available"},
    }


@app.get("/approvals")
def list_approvals(http_request: Request):
    """List pending high-impact actions for the authenticated client session."""
    return {"approvals": _require_agent(http_request).pending_approvals()}


@app.post("/approvals/{request_id}")
def decide_approval(
    request_id: str,
    decision: ApprovalDecisionRequest,
    http_request: Request,
):
    """Approve or reject one pending action and execute only after approval."""
    agent = _require_agent(http_request)
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
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/runtime/reload")
def reload_runtime():
    """Reload provider configuration and clear cached HTTP sessions."""
    cleared_sessions = runtime.session_count
    if not runtime.refresh():
        raise HTTPException(status_code=503, detail=runtime.error or "Runtime reload failed")
    return {
        "status": "ok",
        "agent_ready": runtime.is_ready,
        "sessions_cleared": cleared_sessions,
        "version": __version__,
    }


@app.post("/chat")
def chat(request: ChatRequest, http_request: Request):
    ip = _get_client_ip(http_request)
    if not _chat_limiter.is_allowed(ip):
        retry = _chat_limiter.get_retry_after(ip)
        logger.warning("Rate limit exceeded on /chat from %s", ip)
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Max 30 requests/minute.",
            headers={"Retry-After": str(int(retry) + 1)},
        )

    logger.info("Chat request from %s (stream=%s)", ip, request.stream)
    agent = _require_agent(http_request)
    if not agent.try_acquire_turn():
        raise HTTPException(status_code=409, detail="This conversation is already processing another request")

    if request.stream:
        return StreamingResponse(
            _sse_generator(agent, request.message, release_turn=True),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    try:
        response = agent.run(request.message)
    except ValueError as e:
        logger.warning("Chat validation error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Chat error: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        agent.release_turn()

    return {
        "response": response,
        "tool_calls": []
    }


@app.post("/chat/stream")
def chat_stream(request: ChatRequest, http_request: Request):
    ip = _get_client_ip(http_request)
    if not _chat_limiter.is_allowed(ip):
        retry = _chat_limiter.get_retry_after(ip)
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Max 30 requests/minute.",
            headers={"Retry-After": str(int(retry) + 1)},
        )

    agent = _require_agent(http_request)
    if not agent.try_acquire_turn():
        raise HTTPException(status_code=409, detail="This conversation is already processing another request")
    return StreamingResponse(
        _sse_generator(agent, request.message, release_turn=True),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _sse_generator(agent, message: str, release_turn: bool = False):
    """Yield one terminal SSE event and optionally release the session turn."""
    terminal_emitted = False
    try:
        for event in agent.stream_run(message):
            if event.get("type") == "done":
                terminal_emitted = True
            yield f"data: {json.dumps(event)}\n\n"
    except Exception:
        logger.exception("SSE stream error")
        yield f'data: {json.dumps({"type": "error", "content": "Stream failed. Check server logs."})}\n\n'
    finally:
        if not terminal_emitted:
            yield f'data: {json.dumps({"type": "done"})}\n\n'
        if release_turn:
            agent.release_turn()


@app.post("/feedback")
def feedback(request: FeedbackRequest, http_request: Request):
    ip = _get_client_ip(http_request)
    if not _feedback_limiter.is_allowed(ip):
        retry = _feedback_limiter.get_retry_after(ip)
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Max 10 feedback requests/minute.",
            headers={"Retry-After": str(int(retry) + 1)},
        )
    logger.info("Feedback received: type=%s from %s", request.type, ip)
    from core.learning import add_feedback
    add_feedback(request.type, request.context)
    return {"status": "ok", "message": "Feedback saved"}


@app.post("/clear")
def clear_history(http_request: Request):
    result = _require_agent(http_request).clear_conversation()
    return {"status": "ok", "message": "History cleared", **result}


@app.get("/history")
def get_history(http_request: Request):
    return {"messages": _require_agent(http_request).history.get()}


@app.get("/audit")
def get_audit_events(http_request: Request, limit: int = 100):
    """Return redacted approval events recorded for the requesting session."""
    return {"events": _require_agent(http_request).audit_events(limit=limit)}


def start(host: str = "127.0.0.1", port: int = 8080):
    """Start the API server."""
    logger.info("Starting HelloChusquis API on %s:%s", host, port)
    print(f"API key: {REQUIRED_API_KEY}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start()
