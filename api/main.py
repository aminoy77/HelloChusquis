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
from pathlib import Path
from core.setup import ensure_config
from core.rate_limiter import RateLimiter
from core.logger import get_logger

logger = get_logger("api")

# --- Token auth config ---
API_KEY_DIR = Path.home() / ".hellochusquis"
API_KEY_FILE = API_KEY_DIR / "api_key.txt"

def _load_or_generate_api_key() -> str:
    """Load existing API key or generate + persist a new one."""
    if key := os.environ.get("HELLOCHUSQUIS_API_KEY", ""):
        return key
    if API_KEY_FILE.exists():
        return API_KEY_FILE.read_text().strip()
    # Generate new key
    API_KEY_DIR.mkdir(parents=True, exist_ok=True)
    key = secrets.token_urlsafe(32)
    API_KEY_FILE.write_text(key + "\n")
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


app = FastAPI(title="HelloChusquis API", version="1.4.3")
app.add_middleware(AuthMiddleware)

# Rate limiters: /chat = 30/min, /feedback = 10/min
_chat_limiter = RateLimiter(requests_per_minute=30)
_feedback_limiter = RateLimiter(requests_per_minute=10)


def _get_client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"

# Ensure config and create shared agent (singleton pattern)
config = ensure_config()

from core.agent import Agent
_agent = Agent(config)


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


@app.get("/")
def root():
    return {"name": "HelloChusquis", "version": "1.4.3", "status": "running"}


@app.get("/health")
def health_check():
    providers = _agent.pool.status()
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
    providers = _agent.pool.status()
    ready = sum(1 for p in providers if p["status"] == "ready")
    if ready == 0:
        raise HTTPException(status_code=503, detail="No providers ready")
    return {"status": "ok", "ready_providers": ready}


@app.get("/health/live")
def liveness_probe():
    return {"status": "ok"}


@app.get("/status")
def get_status():
    providers = _agent.pool.status()
    return {
        "providers": providers,
        "plugins": [p["name"] for p in _agent.plugins],
        "memory": {"sessions": "N/A", "summary": "Available"}
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

    if request.stream:
        return StreamingResponse(
            _sse_generator(request.message),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    try:
        response = _agent.run(request.message)
    except ValueError as e:
        logger.warning("Chat validation error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Chat error: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")

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

    return StreamingResponse(
        _sse_generator(request.message),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _sse_generator(message: str):
    """Generator that yields SSE-formatted events from agent stream_run."""
    try:
        for event in _agent.stream_run(message):
            yield f"data: {json.dumps(event)}\n\n"
    except Exception as e:
        logger.error("SSE stream error: %s", e)
        yield f'data: {json.dumps({"type": "error", "message": "Stream failed: " + str(e)})}\n\n'
    finally:
        yield f'data: {json.dumps({"type": "done"})}\n\n'


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
def clear_history():
    _agent.history.clear()
    return {"status": "ok", "message": "History cleared"}


@app.get("/history")
def get_history():
    return {"messages": _agent.history.get()}


def start(host: str = "127.0.0.1", port: int = 8080):
    """Start the API server."""
    logger.info("Starting HelloChusquis API on %s:%s", host, port)
    print(f"API key: {REQUIRED_API_KEY}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start()
