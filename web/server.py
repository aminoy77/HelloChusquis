import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.responses import StreamingResponse
import uvicorn
import json
import hashlib
import hmac
import secrets
import urllib.parse
from pathlib import Path
from typing import Literal

from core.setup import ensure_config
from core.agent import Agent
from core.plugins import load_plugins
import core.db_memory as db_memory
from core.learning import load_learnings, add_feedback
from core.rate_limiter import RateLimiter
from core.logger import get_logger

logger = get_logger("web")

# --- Token auth config ---
_AUTH_DIR = Path.home() / ".hellochusquis"
_AUTH_KEY_FILE = _AUTH_DIR / "api_key.txt"


def _load_or_create_api_key() -> str:
    """Load existing API key or generate and persist a new one."""
    env_key = os.environ.get("HELLOCHUSQUIS_API_KEY", "")
    if env_key:
        return env_key

    if _AUTH_KEY_FILE.exists():
        existing = _AUTH_KEY_FILE.read_text().strip()
        if existing:
            return existing

    # Auto-generate and persist
    _AUTH_DIR.mkdir(parents=True, exist_ok=True)
    token = secrets.token_urlsafe(32)
    _AUTH_KEY_FILE.write_text(token + "\n")
    return token


REQUIRED_API_KEY = _load_or_create_api_key()
# Auth is opt-in. The web UI exposes an agent with shell access; leaving it
# open on localhost still allows CSRF/PNA/DNS-rebinding-driven attacks from
# any website or local process. For trusted local use the app opens without a
# key. Set HELLOCHUSQUIS_AUTH=1 (or true/yes/on) to require the access key
# (trusted LAN / kiosk / shared machines).
_AUTH_ENABLED = os.environ.get("HELLOCHUSQUIS_AUTH", "").strip().lower() in ("1", "true", "yes", "on")
AUTH_ENABLED = _AUTH_ENABLED


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

        # Auth is disabled by default (local web UI)
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


app = FastAPI()
app.add_middleware(AuthMiddleware)
config = ensure_config()
agent = Agent(config)

_chat_limiter = RateLimiter(requests_per_minute=30)


# --- Request models ---

class MessageRequest(BaseModel):
    message: str
    provider: str | None = None
    model: str | None = None


class FeedbackRequest(BaseModel):
    type: Literal["positive", "negative"]
    context: str = ""


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
    providers = agent.pool.status()
    total = len(providers)
    ready = sum(1 for p in providers if p["status"] == "ready")
    return {
        "status": "ok",
        "version": "1.4.3",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "providers": {"total": total, "ready": ready},
    }


@app.get("/health/ready")
def readiness_probe():
    providers = agent.pool.status()
    ready = sum(1 for p in providers if p["status"] == "ready")
    if ready == 0:
        raise HTTPException(status_code=503, detail="No providers ready")
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

    if user_input == "/clear":
        agent.history.clear()
        return {"response": "Historial limpiado.", "tool_calls": []}

    if user_input == "/status":
        status = agent.pool.status()
        lines = [f"{'✓' if p['status'] == 'ready' else '✗'} {p['name']} — {p['model']}" for p in status]
        return {"response": "\n".join(lines), "tool_calls": []}

    tool_calls_log = []
    original_dispatch = agent._dispatch_tool

    def logged_dispatch(name, args):
        result = original_dispatch(name, args)
        tool_calls_log.append({
            "tool": name,
            "args": args,
            "success": result.success,
            "output": result.output[:200]
        })
        return result

    agent._dispatch_tool = logged_dispatch

    try:
        response = agent.run(user_input, provider=req.provider, model=req.model)
    except RuntimeError as e:
        logger.error("Chat error: %s", e)
        response = f"Error: {e}"
    finally:
        agent._dispatch_tool = original_dispatch

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

    if user_input == "/clear":
        agent.history.clear()
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
        except RuntimeError as e:
            yield f"data: {json.dumps({'type': 'error', 'content': f'Error: {e}'})}\n\n"
        except Exception as e:
            logger.exception("Stream failed")
            yield f"data: {json.dumps({'type': 'error', 'content': f'Error: {e}'})}\n\n"

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
def clear_history():
    """Clear agent conversation history."""
    agent.history.clear()
    return {"status": "ok", "message": "History cleared"}


@app.post("/config")
def update_config(req: ConfigRequest):
    """Accept config updates from frontend (non-destructive)."""
    return {"status": "ok"}


@app.get("/status")
def status():
    providers = agent.pool.status()
    plugins = [{"name": p["name"]} for p in agent.plugins]
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
def models(provider: str = "", refresh: bool = False):
    """Available models for a provider (cached server-side, ~5 min TTL)."""
    known_names = {p["name"] for p in agent.pool.status()}
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
def update_provider(data: ProviderUpdate):
    """Update provider configuration."""
    # Validate provider name exists
    known_names = {p["name"] for p in agent.pool.status()}
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
        return {"status": "ok", "provider": data.name}
    except Exception:
        logger.exception("update-provider failed")
        raise HTTPException(status_code=500, detail="Failed to update provider")


def start(host: str = "127.0.0.1", port: int = 8000):
    if AUTH_ENABLED:
        logger.info("Auth enabled — %s", _auth_hint())
    else:
        logger.info("Auth disabled — set HELLOCHUSQUIS_AUTH=1 to protect the web UI")
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    start()
