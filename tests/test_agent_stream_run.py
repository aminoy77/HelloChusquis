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


def test_stream_run_yields_tool_result_events(monkeypatch):
    """Tool execution in stream_run must surface results as events (TUI)."""
    import core.agent as agent_mod
    from tools.base import ToolResult

    agent = Agent.__new__(Agent)
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
    agent._build_messages = lambda: [{"role": "user", "content": "do it"}]
    agent.tools_schema = [{"type": "function", "function": {"name": "echo_tool"}}]
    agent.tool_policy = type("P", (), {"is_tool_allowed": lambda self, n: True})()
    agent.security_auditor = type("A", (), {"audit_tool_call": lambda self, n, a: []})()
    agent.loop_detector = type("L", (), {
        "detect": lambda self, s, n, a: type("R", (), {"stuck": False})(),
        "record_call": lambda self, s, n, a: None,
        "record_outcome": lambda self, s, n, a, **k: None})()
    agent.plugins = []
    agent._loop_session_state = {}
    agent._authorization_denied_result = lambda *a, **k: None
    agent._approval_required_result = lambda *a, **k: None
    agent._safe_dispatch = lambda name, args: ToolResult(success=True, output="echoed: hi")
    agent._handle_active_learning_trigger = lambda *a, **k: None

    monkeypatch.setattr(agent_mod, "memory", type("M", (), {
        "recall_context": staticmethod(lambda *a, **k: None),
        "save_turn": staticmethod(lambda *a, **k: None),
        "_get_store": staticmethod(lambda: None)}), raising=False)

    # First round: tool call. Second round: final answer.
    rounds = iter([
        [{"type": "tool_calls", "tool_calls": [
            {"id": "c1", "function": {"name": "echo_tool", "arguments": "{}"}}]}],
        [{"type": "chunk", "content": "done"}],
    ])
    agent.pool = type("P", (), {"chat_stream": lambda self, msgs, **k: iter(next(rounds))})()

    events = list(agent.stream_run("do it"))
    results = [e for e in events if e.get("type") == "tool_result"]
    assert results, f"no tool_result event in {[e['type'] for e in events]}"
    r = results[0]
    assert r["tool"] == "echo_tool"
    assert r["success"] is True
    assert r["output"] == "echoed: hi"
