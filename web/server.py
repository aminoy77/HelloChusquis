import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
import json
from pathlib import Path

from core.setup import ensure_config
from core.agent import Agent
from core.plugins import load_plugins
from core.memory import load_summary, SESSIONS_DIR
from core.learning import load_learnings

app = FastAPI()
config = ensure_config()
agent = Agent(config)


class MessageRequest(BaseModel):
    message: str


@app.get("/", response_class=HTMLResponse)
async def root():
    html_path = Path(__file__).parent / "index.html"
    return html_path.read_text()


@app.post("/chat")
async def chat(req: MessageRequest):
    user_input = req.message.strip()

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
        response = f"Error: {e}"
    finally:
        agent._dispatch_tool = original_dispatch

    return {"response": response, "tool_calls": tool_calls_log}


@app.get("/status")
async def status():
    providers = agent.pool.status()
    plugins = [{"name": p["name"]} for p in agent.plugins]
    summary = load_summary()
    sessions = len(list(SESSIONS_DIR.glob("*.json"))) if SESSIONS_DIR.exists() else 0
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
        }
    }


def start():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")


if __name__ == "__main__":
    start()