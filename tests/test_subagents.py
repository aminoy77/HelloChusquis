"""Tests for the subagent system (core/subagents.py + agents/*/AGENT.md)."""
import re
import threading
import time
from pathlib import Path

import pytest

from tools.base import ToolResult


class FakePool:
    """Scripted pool: pops canned responses, tracks peak concurrency."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = 0
        self.peak = 0
        self._active = 0
        self._lock = threading.Lock()
        self.last_kwargs = {}

    def chat_with_retry(self, messages, tools=None, max_retries=3, provider_name=None, model=None):
        with self._lock:
            self._active += 1
            self.peak = max(self.peak, self._active)
            self.last_kwargs = {"provider_name": provider_name, "model": model}
            self.last_messages = list(messages)
        try:
            time.sleep(0.02)
            self.calls += 1
            if not self.script:
                return {"choices": [{"message": {"content": "done"}}]}
            return self.script.pop(0)
        finally:
            with self._lock:
                self._active -= 1


def _tool_call(name, args=None, call_id="call_1"):
    import json
    return {
        "choices": [{
            "message": {
                "content": "",
                "tool_calls": [{
                    "id": call_id,
                    "function": {"name": name, "arguments": json.dumps(args or {})},
                }],
            }
        }]
    }


def _final(text):
    return {"choices": [{"message": {"content": text}}]}


def _ok_dispatch(name, args):
    return ToolResult(success=True, output=f"{name} ok")


def test_registry_has_twelve_valid_defs():
    from core import subagents
    assert len(subagents.BUILTIN_DEFS) == 12
    names = [d.name for d in subagents.BUILTIN_DEFS]
    assert len(set(names)) == 12
    assert all(re.fullmatch(r"[a-z0-9-]+", n) for n in names)
    assert all(d.description and d.instructions for d in subagents.BUILTIN_DEFS)


def test_def_tools_exist_in_real_schema():
    from core import subagents
    from core.agent import _build_tools_schema
    real = {f["function"]["name"] for f in _build_tools_schema([])}
    for d in subagents.BUILTIN_DEFS:
        assert set(d.tools) <= real, f"{d.name} references unknown tools"


def test_run_one_returns_output():
    from core import subagents
    pool = FakePool([_final("answer here")])
    d = next(d for d in subagents.BUILTIN_DEFS if d.name == "researcher")
    res = subagents.run_one(pool, [], _ok_dispatch, d, "task text")
    assert res.output == "answer here"
    assert res.steps_used == 1
    assert res.truncated is False


def test_run_one_runs_allowed_tool_and_blocks_other():
    from core import subagents
    pool = FakePool([
        _tool_call("web_search", {"query": "x"}),
        _tool_call("shell", {"command": "rm -rf /"}),
        _final("synthesis"),
    ])
    d = next(d for d in subagents.BUILTIN_DEFS if d.name == "researcher")
    seen = []

    def dispatch(name, args):
        seen.append(name)
        return ToolResult(success=True, output="hit")

    res = subagents.run_one(pool, [], dispatch, d, "t")
    assert seen == ["web_search"]  # shell blocked in harness, never dispatched
    assert res.tool_calls == 2  # executed + blocked attempt both counted
    assert res.output == "synthesis"


def test_transcript_budget_truncates():
    from core import subagents
    pool = FakePool([_final("x" * 5000)])
    d = next(d for d in subagents.BUILTIN_DEFS if d.name == "coder")
    res = subagents.run_one(pool, [], _ok_dispatch, d, "t", max_tokens=10)
    assert res.truncated is True


def test_fanout_respects_concurrency_cap():
    from core import subagents
    pool = FakePool([_final("ok")] * 10)
    d = next(d for d in subagents.BUILTIN_DEFS if d.name == "reviewer")
    jobs = [{"name": "reviewer", "task": f"t{i}"} for i in range(10)]
    results = subagents.fanout(pool, [], _ok_dispatch, d, jobs, max_concurrent=3)
    assert len(results) == 10
    assert all(r.output == "ok" for r in results)
    assert pool.peak <= 3


def test_custom_rejects_bad_name_and_unknown_tool():
    from core import subagents
    with pytest.raises(ValueError):
        subagents.parse_custom({"name": "Bad Name!", "description": "x", "instructions": "y"})
    with pytest.raises(ValueError):
        subagents.parse_custom({
            "name": "mine", "description": "x", "instructions": "y",
            "tools": ["no_such_tool"],
        })


def test_prompt_section_lists_all_agents():
    from core import subagents
    section = subagents.subagents_prompt_section()
    for d in subagents.BUILTIN_DEFS:
        assert d.name in section
    assert "unlimited" in section.lower()


def test_model_routing_passes_provider_and_model():
    from core import subagents
    pool = FakePool([_final("ok")])
    d = next(d for d in subagents.BUILTIN_DEFS if d.name == "reviewer")
    subagents.run_one(pool, [], _ok_dispatch, d, "t",
                      provider="openrouter", model="cheap-1")
    assert pool.last_kwargs == {"provider_name": "openrouter", "model": "cheap-1"}


def test_nested_subagent_spawn_blocked():
    from core import subagents
    pool = FakePool([_tool_call("subagent", {"action": "list"}), _final("done")])
    d = next(d for d in subagents.BUILTIN_DEFS if d.name == "coder")
    seen = []

    def dispatch(name, args):
        seen.append(name)
        return ToolResult(success=True, output="x")

    res = subagents.run_one(pool, [], dispatch, d, "t")
    assert seen == []  # flat hierarchy: never dispatched
    assert res.output == "done"


def test_scoped_dispatch_contains_files_and_blocks_shell():
    import tempfile
    from core import subagents
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "in.txt").write_text("x")
        calls = []

        def dispatch(name, args):
            calls.append(name)
            return ToolResult(success=True, output="ok")

        scoped = subagents.scoped_dispatch(dispatch, root)
        assert scoped("files", {"action": "read", "path": str(root / "in.txt")}).success
        assert not scoped("files", {"action": "read", "path": "/etc/passwd"}).success
        assert not scoped("shell", {"command": "ls"}).success
        assert not scoped("code", {"code": "1+1"}).success
        assert calls == ["files"]


def test_worktree_helper_creates_and_cleans():
    import subprocess
    from core import subagents
    repo = Path(__file__).resolve().parent.parent
    with subagents.git_worktree(repo) as wt:
        assert wt is not None and (wt / ".git").exists()
        path = str(wt)
    assert not Path(path).exists()
    leftovers = subprocess.run(["git", "worktree", "list", "--porcelain"],
                               capture_output=True, text=True, cwd=repo).stdout
    assert path not in leftovers


def test_isolated_run_blocks_shell_and_reports_diff():
    from core import subagents
    pool = FakePool([_tool_call("shell", {"command": "ls"}), _final("done")])
    d = next(d for d in subagents.BUILTIN_DEFS if d.name == "coder")
    seen = []

    def dispatch(name, args):
        seen.append(name)
        return ToolResult(success=True, output="x")

    repo = Path(__file__).resolve().parent.parent
    res = subagents.run_one(pool, [], dispatch, d, "t", isolated=True, repo=repo)
    assert seen == []  # shell/code can't be contained: blocked when isolated
    assert "worktree" in res.output.lower()


def test_agent_md_files_match_registry():
    from core import subagents
    root = Path(__file__).resolve().parent.parent / "agents"
    assert root.is_dir()
    for d in subagents.BUILTIN_DEFS:
        md = root / d.name / "AGENT.md"
        assert md.is_file(), f"missing {md}"
        text = md.read_text()
        assert d.name in text and "tools" in text.lower()


def test_chain_threads_prior_output_in_order():
    from core import subagents
    pool = FakePool([_final("answer1"), _final("answer2")])
    jobs = [{"name": "planner", "task": "break it down"},
            {"name": "reviewer", "task": "critique it"}]
    results = subagents.chain(pool, [], _ok_dispatch, jobs)
    assert [r.output for r in results] == ["answer1", "answer2"]
    assert pool.calls == 2
    user_texts = [m["content"] for m in pool.last_messages if m["role"] == "user"]
    assert any("answer1" in t for t in user_texts)


def test_chain_halts_on_first_failure():
    from core import subagents
    pool = FakePool([_final("ok1"), {"choices": []}])
    jobs = [{"name": "planner", "task": "t1"},
            {"name": "reviewer", "task": "t2"},
            {"name": "reviewer", "task": "t3"}]
    results = subagents.chain(pool, [], _ok_dispatch, jobs)
    assert len(results) == 2
    assert results[0].ok and not results[1].ok
    assert pool.calls == 2


def test_result_carries_duration():
    from core import subagents
    pool = FakePool([_final("ok")])
    d = next(d for d in subagents.BUILTIN_DEFS if d.name == "planner")
    res = subagents.run_one(pool, [], _ok_dispatch, d, "t")
    assert res.duration_s >= 0


def test_fanout_fail_fast_skips_rest():
    from core import subagents
    pool = FakePool([_final("ok"), {"choices": []}, _final("never")])
    jobs = [{"name": "reviewer", "task": f"t{i}"} for i in range(3)]
    results = subagents.fanout(pool, [], _ok_dispatch, None, jobs,
                               max_concurrent=1, fail_fast=True)
    assert [r.ok for r in results] == [True, False]
    assert pool.calls == 2


def test_fanout_without_fail_fast_runs_all():
    from core import subagents
    pool = FakePool([_final("ok"), {"choices": []}, _final("ok3")])
    jobs = [{"name": "reviewer", "task": f"t{i}"} for i in range(3)]
    results = subagents.fanout(pool, [], _ok_dispatch, None, jobs,
                               max_concurrent=1)
    assert len(results) == 3
    assert pool.calls == 3


def test_events_sequence_on_run_with_tool():
    import threading
    from core import subagents
    pool = FakePool([_tool_call("web_search", {"query": "x"}), _final("done")])
    d = next(d for d in subagents.BUILTIN_DEFS if d.name == "researcher")
    events, lock = [], threading.Lock()

    def on_event(ev):
        with lock:
            events.append(ev)

    res = subagents.run_one(pool, [], _ok_dispatch, d, "t", on_event=on_event)
    assert [e["type"] for e in events] == ["run_start", "tool_call", "run_finish"]
    assert events[1]["tool"] == "web_search" and events[1]["ok"] is True
    assert events[2]["ok"] is True and res.ok


def test_cache_hit_skips_second_call():
    from core import subagents
    subagents.cache_clear()
    pool = FakePool([_final("same answer"), _final("must not run")])
    d = next(d for d in subagents.BUILTIN_DEFS if d.name == "planner")
    r1 = subagents.run_one(pool, [], _ok_dispatch, d, "cache-me-task", cache_ttl_s=3600)
    r2 = subagents.run_one(pool, [], _ok_dispatch, d, "cache-me-task", cache_ttl_s=3600)
    assert pool.calls == 1
    assert r1.cached is False and r2.cached is True
    assert r2.output == "same answer"


def test_cache_miss_on_different_task():
    from core import subagents
    subagents.cache_clear()
    pool = FakePool([_final("a"), _final("b")])
    d = next(d for d in subagents.BUILTIN_DEFS if d.name == "planner")
    subagents.run_one(pool, [], _ok_dispatch, d, "task-alpha", cache_ttl_s=3600)
    subagents.run_one(pool, [], _ok_dispatch, d, "task-beta", cache_ttl_s=3600)
    assert pool.calls == 2


def test_cache_never_stores_tool_runs():
    from core import subagents
    subagents.cache_clear()
    script = [_tool_call("web_search", {"query": "x"}), _final("live"),
              _tool_call("web_search", {"query": "x"}), _final("live2")]
    pool = FakePool(script)
    d = next(d for d in subagents.BUILTIN_DEFS if d.name == "researcher")
    r1 = subagents.run_one(pool, [], _ok_dispatch, d, "fresh-task", cache_ttl_s=3600)
    r2 = subagents.run_one(pool, [], _ok_dispatch, d, "fresh-task", cache_ttl_s=3600)
    assert pool.calls == 4  # tool output reflects world state: always re-run
    assert r1.cached is False and r2.cached is False


def test_cache_entry_expires():
    import time
    from core import subagents
    subagents.cache_clear()
    pool = FakePool([_final("v1"), _final("v2")])
    d = next(d for d in subagents.BUILTIN_DEFS if d.name == "planner")
    subagents.run_one(pool, [], _ok_dispatch, d, "aging-task", cache_ttl_s=3600)
    for entry in subagents._RESULT_CACHE.values():
        entry["expires_at"] = time.time() - 1
    r2 = subagents.run_one(pool, [], _ok_dispatch, d, "aging-task", cache_ttl_s=3600)
    assert pool.calls == 2 and r2.output == "v2" and r2.cached is False
