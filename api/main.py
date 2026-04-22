from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from core.setup import ensure_config
import json

app = FastAPI(title="HelloChusquis API", version="1.0.0")

# Ensure config
config = ensure_config()


class ChatRequest(BaseModel):
    message: str
    stream: bool = False


class FeedbackRequest(BaseModel):
    type: str  # positive or negative
    context: str


@app.get("/")
def root():
    return {"name": "HelloChusquis", "version": "1.0.0", "status": "running"}


@app.get("/status")
def get_status():
    from core.agent import Agent
    agent = Agent(config)
    providers = agent.pool.status()
    return {
        "providers": providers,
        "plugins": [p["name"] for p in agent.plugins],
        "memory": {"sessions": "N/A", "summary": "Available"}
    }


@app.post("/chat")
def chat(request: ChatRequest):
    from core.agent import Agent
    from core.history import History
    
    history = History()
    history.add("user", request.message)
    
    agent = Agent(config)
    response = agent.run(request.message)
    
    return {
        "response": response,
        "tool_calls": []
    }


@app.post("/feedback")
def feedback(request: FeedbackRequest):
    from core.learning import add_feedback
    add_feedback(request.type, request.context)
    return {"status": "ok", "message": "Feedback saved"}


@app.post("/clear")
def clear_history():
    from core.history import History
    history = History()
    history.clear()
    return {"status": "ok", "message": "History cleared"}


@app.get("/history")
def get_history():
    from core.history import History
    history = History()
    return {"messages": history.get()}


def start(host: str = "0.0.0.0", port: int = 8080):
    """Start the API server."""
    print(f"Starting HelloChusquis API on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start()