"""Regression tests for plan-stuck bug + runaway loop fixes."""
from types import SimpleNamespace

import pytest

from core.agent import Agent
from core.planner import execute_plan


def _agent():
    agent = Agent.__new__(Agent)
    agent.pool = None
    agent.history = SimpleNamespace(add=lambda *a: None, messages=[],
                                    get_token_count=lambda m: 0,
                                    optimize_context=lambda max_tokens=0: [],
                                    get_user_inputs=lambda: ["goal"])
    agent.session_manager = SimpleNamespace(append_message=lambda *a, **k: None)
    agent._session_id = "t"
    agent.tools_schema = None
    agent._build_messages = lambda: [{"role": "user", "content": "hi"}]
    return agent


def test_run_tool_loop_capped(monkeypatch):
    agent = _agent()
    calls = {"n": 0}

    def fake_chat(*a, **k):
        calls["n"] += 1
        return {"choices": [{"message": {"tool_calls": [
            {"id": "1", "function": {"name": "shell", "arguments": "{}"}}]}}]}

    agent.pool = SimpleNamespace(chat_with_retry=fake_chat)
    agent._known_tool_names = lambda: {"shell"}
    agent.tool_policy = SimpleNamespace(is_tool_allowed=lambda t: False)
    agent.security_auditor = SimpleNamespace(audit_tool_call=lambda *a: [])
    agent.loop_detector = SimpleNamespace(detect=lambda *a: SimpleNamespace(stuck=False),
                                          record_call=lambda *a: None,
                                          record_outcome=lambda *a, **k: None)
    agent._loop_session_state = None
    agent._authorization_denied_result = lambda *a: None
    agent._approval_required_result = lambda *a: None
    agent._safe_dispatch = lambda *a, **k: SimpleNamespace(success=False, output="", error="denied")
    agent._handle_active_learning_trigger = lambda *a: None

    result = agent.run("do thing")
    assert "stopped after 30" in result.lower()
    assert calls["n"] <= 31  # capped, not infinite


def test_execute_plan_replan_depth_capped(monkeypatch):
    import core.planner as planner

    agent = _agent()
    runs = {"n": 0}
    agent.run = lambda step: runs.__setitem__("n", runs["n"] + 1) or (_ for _ in ()).throw(
        RuntimeError("all providers failed"))
    monkeypatch.setattr(planner, "generate_plan", lambda *a, **k: ["step A", "step B"])
    monkeypatch.setattr(planner.console, "print", lambda *a, **k: None)

    execute_plan(["step A"], agent)  # must terminate, not recurse forever
    assert runs["n"] < 10


def test_execute_plan_notify_callback():
    agent = _agent()
    agent.run = lambda step: f"did {step}"
    seen = []
    execute_plan(["a", "b"], agent, notify=lambda msg: seen.append(msg))
    assert any("1/2" in m for m in seen) and any("2/2" in m for m in seen)
