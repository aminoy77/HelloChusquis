import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import uvicorn
import json
import hashlib
import hmac
from pathlib import Path

from core.setup import ensure_config
from core.agent import Agent
from core.plugins import load_plugins
import core.db_memory as db_memory
from core.learning import load_learnings
from core.rate_limiter import RateLimiter
from core.logger import get_logger

logger = get_logger("web")

# --- Token auth config ---
REQUIRED_API_KEY = os.environ.get("HELLOCHUSQUIS_API_KEY", "")
AUTH_ENABLED = bool(REQUIRED_API_KEY)


def _verify_token(token: str) -> bool:
    """Constant-time token comparison to prevent timing attacks."""
    if not AUTH_ENABLED:
        return True
    return hmac.compare_digest(token, REQUIRED_API_KEY)


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for login page (GET /)
        if request.method == "GET" and request.url.path == "/":
            return await call_next(request)

        # Skip auth for auth bootstrap and health probes
        if request.url.path in ("/auth/check", "/auth/verify", "/health", "/health/ready", "/health/live"):
            return await call_next(request)

        # If auth disabled, pass through
        if not AUTH_ENABLED:
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


class MessageRequest(BaseModel):
    message: str


@app.get("/", response_class=HTMLResponse)
async def root():
    html_path = Path(__file__).parent / "index.html"
    return html_path.read_text()


@app.get("/auth/check")
def auth_check():
    """Tell the frontend whether auth is required and if a token works."""
    auth_required = AUTH_ENABLED
    return {"auth_required": auth_required}


@app.post("/auth/verify")
def auth_verify(req: MessageRequest):
    """Verify a bearer token. Returns 200 if valid."""
    if not AUTH_ENABLED:
        return {"status": "ok"}
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
async def chat(req: MessageRequest, http_request: Request):
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
        response = agent.run(user_input)
    except RuntimeError as e:
        logger.error("Chat error: %s", e)
        response = f"Error: {e}"
    finally:
        agent._dispatch_tool = original_dispatch

    return {"response": response, "tool_calls": tool_calls_log}


@app.get("/status")
async def status():
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


class ProviderUpdate(BaseModel):
    name: str
    key: str = ""
    base: str = ""
    model: str = ""


@app.post("/update-provider")
async def update_provider(data: ProviderUpdate):
    """Update provider configuration."""
    try:
        if data.key:
            agent.pool.update_api_key(data.name, data.key)
        if data.base:
            agent.pool.update_base_url(data.name, data.base)
        if data.model:
            agent.pool.update_model(data.name, data.model)
        return {"status": "ok", "provider": data.name}
    except Exception as e:
        logger.error("Provider update failed for %s: %s", data.name, e)
        return {"status": "error", "message": "Could not update provider"}


def start(host: str = "127.0.0.1", port: int = 8000):
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    start()