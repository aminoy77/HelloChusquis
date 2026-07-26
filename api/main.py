from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
from core.setup import ensure_config
import json
from core.rate_limiter import RateLimiter
from core.logger import get_logger

logger = get_logger("api")

app = FastAPI(title="HelloChusquis API", version="1.4.3")

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


class FeedbackRequest(BaseModel):
    type: str  # positive or negative
    context: str


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
    for event in _agent.stream_run(message):
        yield f"data: {json.dumps(event)}\n\n"


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


def start(host: str = "0.0.0.0", port: int = 8080):
    """Start the API server."""
    logger.info("Starting HelloChusquis API on %s:%s", host, port)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start()