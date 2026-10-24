"""Tests for real streaming in Agent.stream_run."""
from core.agent import Agent
from core.provider import ProviderPool


def test_stream_run_yields_real_chunks(monkeypatch):
    agent = Agent.__new__(Agent)
    agent.pool = ProviderPool.__new__(ProviderPool)
    agent.history = type("H", (), {
        "add": staticmethod(lambda role, content: None),
        "messages": [],
        "get_token_count": staticmethod(lambda msgs: 0),
        "optimize_context": staticmethod(lambda max_tokens=0: []),
    })()
    agent.session_manager = type("S", (), {
        "append_message": staticmethod(lambda *a, **k: None)})()
    agent._session_id = "t"
    agent._pending_tool_results = []
    agent.tools_schema = None
    agent._build_messages = lambda: [{"role": "user", "content": "hello"}]

    events_in = [{"type": "reasoning", "content": "hmm"},
                 {"type": "chunk", "content": "Hi"},
                 {"type": "chunk", "content": " there"}]
    monkeypatch.setattr(ProviderPool, "chat_stream",
                        lambda self, msgs, **k: iter(events_in + [{"type": "done"}]))

    saved = {}
    import core.agent as agent_mod
    monkeypatch.setattr(agent_mod, "memory", type("M", (), {
        "save_turn": staticmethod(lambda *a, **k: saved.setdefault("turn", True)),
        "recall_context": staticmethod(lambda *a, **k: None)}), raising=False)

    events = list(agent.stream_run("hello"))
    kinds = [e["type"] for e in events]
    assert kinds == ["reasoning", "chunk", "chunk", "done"]
    assert saved.get("turn")
