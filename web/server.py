import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.responses import StreamingResponse
import uvicorn
import json
import hmac
import re
import secrets
import urllib.parse
from pathlib import Path
from typing import Literal

from core.runtime import AgentNotReadyError, AgentRuntime
from core.version import __version__
import core.db_memory as db_memory
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
    """Human-readable hint about where the API key lives."""
    if os.environ.get("HELLOCHUSQUIS_API_KEY"):
        return "Set via the HELLOCHUSQUIS_API_KEY environment variable."
    if _AUTH_KEY_FILE.exists():
        return f"Stored in {_AUTH_KEY_FILE}"
    return f"Generate one by starting the server (saved to {_AUTH_KEY_FILE})"


def _verify_token(token: str) -> bool:
    """Constant-time token comparison to prevent timing attacks."""
    return hmac.compare_digest(token, REQUIRED_API_KEY)


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
        if not _verify_token(token):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid API key"},
            )
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add defensive headers to every web response, including auth failures."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), camera=()")
        return response


app = FastAPI()
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
        session_id = _session_id(http_request) if http_request is not None else None
        return runtime.get(session_id=session_id)
    except AgentNotReadyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


_chat_limiter = RateLimiter(requests_per_minute=30)


# --- Request models ---

class MessageRequest(BaseModel):
    message: str
    provider: str | None = None
    model: str | None = None


class FeedbackRequest(BaseModel):
    type: Literal["positive", "negative"]
    context: str = ""


class ApprovalDecisionRequest(BaseModel):
    approve: bool


class ConfigRequest(BaseModel):
    data: dict = Field(default_factory=dict)


# --- Routes ---

@app.get("/", response_class=HTMLResponse)
async def root():
    html_path = Path(__file__).parent / "index.html"
    return html_path.read_text()


@app.get("/auth/check")
def auth_check():
    """Tell the frontend whether auth is required (and where the key lives)."""
    return {
        "auth_required": AUTH_ENABLED,
        "key_hint": _auth_hint() if AUTH_ENABLED else "",
    }


@app.post("/auth/verify")
def auth_verify(req: MessageRequest):
    """Verify a bearer token. Returns 200 if valid."""
    if _verify_token(req.message):
        return {"status": "ok"}
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
        raise HTTPException(status_code=503, detail=readiness.get("error", "No providers ready"))
    providers = readiness["providers"]
    ready = sum(1 for provider in providers if provider["status"] == "ready")
    return {"status": "ok", "ready_providers": ready}


@app.get("/health/live")
def liveness_probe():
    return {"status": "ok"}


@app.post("/chat")
def chat(req: MessageRequest, http_request: Request):
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
        agent.clear_conversation()
        return {"response": "Historial limpiado.", "tool_calls": []}

    if user_input == "/status":
        status = agent.pool.status()
        lines = [f"{'✓' if p['status'] == 'ready' else '✗'} {p['name']} — {p['model']}" for p in status]
        return {"response": "\n".join(lines), "tool_calls": []}

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
        response = f"Error: {e}"

    return {"response": response, "tool_calls": tool_calls_log}


@app.post("/chat/stream")
def chat_stream(req: MessageRequest, http_request: Request):
    """SSE streaming endpoint. Same contract as /chat but yields chunks."""
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
        agent.clear_conversation()
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

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/feedback")
def feedback(req: FeedbackRequest):
    """Accept positive/negative feedback from frontend."""
    add_feedback(req.type, req.context)
    return {"status": "ok"}


@app.post("/clear")
def clear_history(http_request: Request):
    """Clear the requesting session's in-memory and persistent history."""
    result = _require_agent(http_request).clear_conversation()
    return {"status": "ok", "message": "History cleared", **result}


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
    name: str
    key: str = ""
    base: str = ""
    model: str = ""


@app.post("/update-provider")
def update_provider(data: ProviderUpdate, http_request: Request):
    """Update provider configuration for the requesting in-memory session only."""
    agent = _require_agent(http_request)
    # Validate provider name exists
    known_names = {provider_status["name"] for provider_status in agent.pool.status()}
    if data.name not in known_names:
        raise HTTPException(status_code=404, detail=f"Provider '{data.name}' not found")

    # Validate base URL scheme if provided
    if data.base:
        parsed = urllib.parse.urlparse(data.base)
        if parsed.scheme not in ("http", "https"):
            raise HTTPException(status_code=400, detail="Base URL must use http or https scheme")
        if not parsed.hostname:
            raise HTTPException(status_code=400, detail="Base URL must have a valid host")

    try:
        if data.key:
            agent.pool.update_api_key(data.name, data.key)
        if data.base:
            agent.pool.update_base_url(data.name, data.base)
        if data.model:
            agent.pool.update_model(data.name, data.model)
        return {"status": "ok", "provider": data.name, "scope": "session"}
    except Exception:
        logger.exception("update-provider failed")
        raise HTTPException(status_code=500, detail="Failed to update provider")


def start(host: str = "127.0.0.1", port: int = 8000):
    if AUTH_ENABLED:
        logger.info("Auth enabled — API key: %s (%s)", REQUIRED_API_KEY, _auth_hint())
    else:
        logger.warning("Auth disabled by HELLOCHUSQUIS_AUTH=0; use only in an isolated local development environment")
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    start()
