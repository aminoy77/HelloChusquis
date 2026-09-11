"""Subagent system: unlimited, cheap, isolated specialists for the main agent.

How it works: the main agent invokes subagents through ONE tool (`subagent`,
actions: list/run/fanout/custom). Each subagent runs in its own isolated
context (own message list), sees only its task, uses only its allowlisted
tools, and returns a distilled summary — never its raw transcript.

Resource model (read this before asking for per-agent RSS caps): subagents
run in-process as bounded synchronous turns sharing the parent's provider
pool — no processes, no 25 MB Python interpreters per agent. An idle queued
subagent costs ~1 KB (a dataclass + task string). A running one costs its
transcript, hard-capped (default 12k tokens ≈ 48 KB; even 100 queued jobs
stay under ~5 MB). Concurrency is capped (default 8, hard max 16), so peak
RAM is bounded no matter how many subagents are invoked. OS-level RSS limits
cannot apply to threads of one process; budgets below are the enforceable
equivalent: max steps, max transcript tokens, timeout, concurrency cap.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterator, Optional

from tools.base import ToolResult

DEFAULT_MAX_STEPS = 12
DEFAULT_MAX_TOKENS = 12000  # ≈48 KB transcript
DEFAULT_TIMEOUT_S = 180
DEFAULT_MAX_CONCURRENT = 8
MAX_CONCURRENT_HARD = 16
FANOUT_ITEM_CHARS = 1500

_NAME_RE = re.compile(r"[a-z0-9-]{1,64}")

# Tool names actually present in core/agent.py schema (tests enforce this).
KNOWN_TOOLS = frozenset({
    "browser", "shell", "code", "web_search", "github", "slack", "discord",
    "docker", "notion", "aws", "twitter", "gmail", "jira", "postgresql",
    "mongodb", "google_calendar", "spotify", "stripe", "twilio", "sendgrid",
    "supabase", "vercel", "sentry", "pagerduty", "datadog", "intercom",
    "contentful", "sanity", "hubspot", "shopify", "mailchimp", "airtable",
    "plaid", "square", "cloudinary", "algolia", "resend", "brevo", "upstash",
    "clerk", "posthog", "launchdarkly", "calendly", "zoom", "files",
    "web_fetch", "speak", "media", "mcp",
})


@dataclass(frozen=True)
class SubAgentDef:
    """One subagent type. tools=None means all parent tools; () means reasoning only."""

    name: str
    description: str
    instructions: str
    tools: Optional[tuple] = ()
    max_steps: int = DEFAULT_MAX_STEPS
    max_tokens: int = DEFAULT_MAX_TOKENS
    timeout_s: int = DEFAULT_TIMEOUT_S
    model: Optional[str] = None  # None = inherit parent model
    provider: Optional[str] = None  # None = inherit parent provider
    isolated: bool = False  # writers run in a throwaway git worktree when True


@dataclass
class SubAgentResult:
    name: str
    task: str
    output: str
    steps_used: int = 0
    tool_calls: int = 0
    transcript_chars: int = 0
    truncated: bool = False
    ok: bool = True
    duration_s: float = 0.0
    cached: bool = False


def _def(name, description, instructions, tools=(), **kw):
    return SubAgentDef(name=name, description=description,
                       instructions=instructions, tools=tuple(tools), **kw)


BUILTIN_DEFS = [
    _def("explorer",
         "Map unfamiliar code: structure, patterns, key files. Read-only.",
         "Explore and report: directory layout, main modules, conventions, entry points. "
         "Skim, don't dump whole files. Stop after ~10 file reads.",
         ["files", "code"]),
    _def("planner",
         "Turn a goal into an ordered, checkable step plan. No tools, pure reasoning.",
         "Output numbered steps, each independently verifiable, with stop criteria. "
         "Prefer fewer, bigger steps over many tiny ones.",
         []),
    _def("researcher",
         "Answer questions from the live web. Returns sources + distilled findings.",
         "Search, fetch, cross-check at least 2 sources for factual claims. "
         "Stop after ~6 searches. Return bullets with URLs, not raw pages.",
         ["web_search", "web_fetch", "browser"]),
    _def("coder",
         "Implement small, well-specified code changes and run them.",
         "Make the minimal diff that satisfies the task. Run the code or tests. "
         "Stop and report if the task needs clarification.",
         ["files", "code", "shell"]),
    _def("reviewer",
         "Critique a diff or file against a checklist. Read-only, no fixes.",
         "Check correctness, edge cases, security, over-engineering. "
         "One line per finding: location, problem, fix. No praise.",
         ["files", "code"]),
    _def("debugger",
         "Reproduce a failure, find the root cause, propose the minimal fix.",
         "Reproduce first, trace to origin, fix at source not symptom. "
         "Show the failing evidence before the fix.",
         ["files", "code", "shell"]),
    _def("tester",
         "Write and run focused tests for given behavior.",
         "One runnable check per behavior, smallest framework-free check that fails "
         "if the logic breaks. Report pass/fail with commands.",
         ["files", "code", "shell"]),
    _def("docs-writer",
         "Write concise docs, READMEs, changelogs from code + context.",
         "Short, accurate, no marketing fluff. Verify names/commands against the code.",
         ["files"]),
    _def("data-analyst",
         "Query data, compute answers, report numbers with method.",
         "Show the query/computation so it can be re-run. Never invent numbers.",
         ["files", "code", "shell", "postgresql", "mongodb"]),
    _def("devops",
         "Inspect and operate local containers, processes, deploys.",
         "Read-only inspection first; mutating ops only as explicitly tasked. "
         "Report exact commands run and their output.",
         ["shell", "docker", "vercel", "github"]),
    _def("security-auditor",
         "Hunt vulnerabilities: secrets, injection, auth gaps, unsafe exec.",
         "Severity-tagged findings with file:line and concrete fix. "
         "No fixes applied, no exploits executed.",
         ["files", "code", "shell", "web_search"]),
    _def("integrator",
         "Read/write third-party services (chat, mail, issues, docs).",
         "Confirm exact payload before any write. Summarize remote state, don't dump it.",
         ["github", "slack", "notion", "gmail", "jira", "web_search"]),
]

BUILTIN_MAP = {d.name: d for d in BUILTIN_DEFS}


def parse_custom(spec: dict) -> SubAgentDef:
    """Validate an inline subagent definition from the main agent. Raises ValueError."""
    if not isinstance(spec, dict):
        raise ValueError("definition must be an object")
    name = str(spec.get("name", ""))
    if not _NAME_RE.fullmatch(name):
        raise ValueError("definition.name must match [a-z0-9-]{1,64}")
    description = str(spec.get("description", "")).strip()
    instructions = str(spec.get("instructions", "")).strip()
    if not description or not instructions:
        raise ValueError("definition needs non-empty description and instructions")
    tools = spec.get("tools", None)
    if tools is None:
        tools_tuple = None  # all parent tools
    else:
        if not isinstance(tools, (list, tuple)):
            raise ValueError("definition.tools must be a list of tool names")
        unknown = set(tools) - KNOWN_TOOLS
        if unknown:
            raise ValueError(f"unknown tools: {sorted(unknown)}")
        tools_tuple = tuple(tools)
    model = spec.get("model") or None
    provider = spec.get("provider") or None
    if model is not None and not isinstance(model, str):
        raise ValueError("definition.model must be a string")
    if provider is not None and not isinstance(provider, str):
        raise ValueError("definition.provider must be a string")
    isolated = spec.get("isolated", False)
    if not isinstance(isolated, bool):
        raise ValueError("definition.isolated must be a boolean")
    return SubAgentDef(name=name, description=description,
                       instructions=instructions, tools=tools_tuple,
                       model=model, provider=provider, isolated=isolated)


def _transcript_len(messages: list) -> int:
    return sum(len(json.dumps(m, default=str)) for m in messages)


# Opt-in result cache: pure-reasoning outputs only (tool runs always re-execute,
# their output reflects world state). Bounded: 128 entries, 8 KB each ≈ 1 MB max.
_CACHE_MAX_ENTRIES = 128
_CACHE_MAX_CHARS = 8000
_RESULT_CACHE: OrderedDict = OrderedDict()
_CACHE_LOCK = threading.Lock()


def cache_clear() -> int:
    """Drop all cached subagent results. Returns entries removed."""
    with _CACHE_LOCK:
        n = len(_RESULT_CACHE)
        _RESULT_CACHE.clear()
        return n


def _cache_key(subdef: SubAgentDef, task: str, model, provider) -> str:
    tools = "ALL" if subdef.tools is None else ",".join(sorted(subdef.tools))
    return json.dumps([subdef.name, task, model, provider, tools])


def _cache_get(key: str):
    with _CACHE_LOCK:
        entry = _RESULT_CACHE.get(key)
        if entry is None:
            return None
        if entry["expires_at"] < time.time():
            del _RESULT_CACHE[key]
            return None
        _RESULT_CACHE.move_to_end(key)
        return entry


def _cache_put(key: str, result: SubAgentResult, ttl_s: float) -> None:
    if len(result.output) > _CACHE_MAX_CHARS:
        return
    with _CACHE_LOCK:
        _RESULT_CACHE[key] = {"output": result.output, "steps": result.steps_used,
                              "expires_at": time.time() + ttl_s}
        _RESULT_CACHE.move_to_end(key)
        while len(_RESULT_CACHE) > _CACHE_MAX_ENTRIES:
            _RESULT_CACHE.popitem(last=False)


def _emit(on_event, payload: dict) -> None:
    if on_event is None:
        return
    try:
        on_event(payload)
    except Exception:
        pass


# Tools that cannot be contained to a directory: always blocked when isolated.
_UNSCOPABLE = frozenset({"shell", "code"})
_PATH_KEYS = ("path", "file", "filename", "filepath", "dir", "directory",
              "cwd", "working_dir", "root")


def scoped_dispatch(dispatch_fn: Callable, root) -> Callable:
    """Wrap a dispatch fn so file writes stay inside root. shell/code blocked."""
    root = Path(root).expanduser().resolve()

    def _scoped(name: str, args: dict) -> ToolResult:
        if name in _UNSCOPABLE:
            return ToolResult(success=False, output="",
                              error=f"Tool '{name}' disabled in isolated worktree (cannot be contained)")
        for key in _PATH_KEYS:
            val = (args or {}).get(key)
            if isinstance(val, str) and val.strip():
                cand = Path(val).expanduser()
                cand = cand if cand.is_absolute() else root / cand
                try:
                    cand.resolve().relative_to(root)
                except ValueError:
                    return ToolResult(success=False, output="",
                                      error=f"Path '{val}' escapes isolated worktree {root}")
        return dispatch_fn(name, args or {})

    return _scoped


@contextmanager
def git_worktree(repo) -> Iterator[Optional[Path]]:
    """Throwaway `git worktree add --detach HEAD`. Yields None when unavailable."""
    repo = Path(repo).expanduser().resolve()
    if not shutil.which("git") or not (repo / ".git").exists():
        yield None
        return
    tmp = Path(tempfile.mkdtemp(prefix="chusqui-sub-"))
    tmp.rmdir()  # worktree add requires a non-existent path
    try:
        r = subprocess.run(["git", "worktree", "add", "--detach", str(tmp), "HEAD"],
                           capture_output=True, text=True, cwd=repo, timeout=60)
        if r.returncode != 0 or not (tmp / ".git").exists():
            shutil.rmtree(tmp, ignore_errors=True)
            yield None
            return
        yield tmp
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(tmp)],
                       capture_output=True, cwd=repo, timeout=60)
        shutil.rmtree(tmp, ignore_errors=True)


def _worktree_summary(wt: Path) -> str:
    try:
        st = subprocess.run(["git", "-C", str(wt), "status", "--porcelain"],
                            capture_output=True, text=True, timeout=30).stdout.strip()
        df = subprocess.run(["git", "-C", str(wt), "diff", "--stat", "HEAD"],
                            capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        return "Worktree diff unavailable."
    if not st:
        return f"Worktree {wt}: no changes."
    body = (st + "\n" + df)[:2000]
    return f"Worktree {wt} changed files:\n{body}"


def run_one(pool, tools_schema: list, dispatch_fn: Callable,
            subdef: SubAgentDef, task: str, *,
            max_steps: Optional[int] = None,
            max_tokens: Optional[int] = None,
            timeout_s: Optional[int] = None,
            model: Optional[str] = None,
            provider: Optional[str] = None,
            isolated: bool = False,
            repo=None,
            on_event=None,
            cache_ttl_s: float = 0) -> SubAgentResult:
    """Run one subagent synchronously with hard budgets. Never raises."""
    t0 = time.perf_counter()
    steps = min(max(max_steps or subdef.max_steps, 1), 50)
    token_budget = min(max(max_tokens or subdef.max_tokens, 500), 100000)
    deadline = time.monotonic() + min(max(timeout_s or subdef.timeout_s, 10), 1800)
    max_chars = token_budget * 4
    model = model or subdef.model
    provider = provider or subdef.provider
    isolated = bool(isolated or subdef.isolated)
    ttl = max(float(cache_ttl_s or 0), 0)

    if ttl > 0:
        hit = _cache_get(_cache_key(subdef, task, model, provider))
        if hit is not None:
            res = SubAgentResult(name=subdef.name, task=task, output=hit["output"],
                                 steps_used=hit["steps"], cached=True,
                                 duration_s=time.perf_counter() - t0)
            _emit(on_event, {"type": "run_start", "name": subdef.name,
                             "task": task[:200], "cached": True})
            _emit(on_event, {"type": "run_finish", "name": subdef.name, "ok": True,
                             "truncated": False, "cached": True,
                             "duration_s": res.duration_s})
            return res

    allowed = set(subdef.tools) if subdef.tools is not None else None
    filtered = [s for s in (tools_schema or [])
                if s.get("function", {}).get("name") in (allowed or set())] or None

    system = (f"You are '{subdef.name}': {subdef.description}\n{subdef.instructions}\n"
              f"Budget: max {steps} tool rounds. Work alone, return only the distilled "
              f"result — no raw dumps, no questions back.")
    notes: list = []
    res = SubAgentResult(name=subdef.name, task=task, output="")
    _ctx = git_worktree(Path(repo or os.getcwd())) if isolated else nullcontext(None)
    wt = _ctx.__enter__()
    dispatch = dispatch_fn
    if isolated:
        if wt is None:
            notes.append("isolation requested but no git worktree available; ran unisolated.")
        else:
            dispatch = scoped_dispatch(dispatch_fn, wt)
            system += (f"\nWork ONLY inside worktree {wt} (absolute paths). "
                       f"shell/code tools are disabled; use files.")
    messages = [{"role": "system", "content": system},
                {"role": "user", "content": task}]
    _emit(on_event, {"type": "run_start", "name": subdef.name,
                     "task": task[:200], "cached": False})
    try:
        while res.steps_used < steps:
            if time.monotonic() > deadline:
                res.truncated = True
                res.output = (res.output or "Stopped: time budget exceeded.") + " [timeout]"
                break
            resp = pool.chat_with_retry(messages, tools=filtered,
                                        provider_name=provider, model=model)
            choices = (resp or {}).get("choices", [])
            if not choices:
                res.ok = False
                res.output = "ERROR: empty provider response"
                break
            msg = choices[0].get("message", {})
            messages.append(msg)
            res.steps_used += 1
            res.transcript_chars = _transcript_len(messages)
            if res.transcript_chars > max_chars:
                res.truncated = True
                res.output = "Stopped: transcript budget exceeded. [truncated]"
                break
            calls = msg.get("tool_calls") or []
            if not calls:
                res.output = msg.get("content") or ""
                break
            for tc in calls:
                fn = tc.get("function", {})
                tname = fn.get("name", "unknown")
                try:
                    targs = json.loads(fn.get("arguments", "{}"))
                except (json.JSONDecodeError, TypeError):
                    targs = {}
                if tname == "subagent":
                    out = ("ERROR: flat hierarchy — subagents cannot spawn "
                           "subagents; do the work yourself.")
                    success = False
                elif allowed is not None and tname not in allowed:
                    out = (f"ERROR: tool '{tname}' not allowed for '{subdef.name}'. "
                           f"Use only: {sorted(allowed) or 'none (reasoning only)'}")
                    success = False
                else:
                    try:
                        r = dispatch(tname, targs)
                        out, success = (r.output, True) if r.success else (f"ERROR: {r.error}", False)
                    except Exception as exc:  # never let a tool kill the subagent
                        out, success = f"ERROR: {type(exc).__name__}: {exc}", False
                res.tool_calls += 1
                _emit(on_event, {"type": "tool_call", "name": subdef.name,
                                 "tool": tname, "ok": success})
                messages.append({"role": "tool", "tool_call_id": tc.get("id", ""),
                                 "content": out})
            res.transcript_chars = _transcript_len(messages)
            if res.transcript_chars > max_chars:
                res.truncated = True
                res.output = (res.output or "Stopped: transcript budget exceeded.") + " [truncated]"
                break
        else:
            res.truncated = True
            res.output = (res.output or "Stopped: step budget exceeded.") + " [truncated]"
    except Exception as exc:
        res.ok = False
        res.output = f"ERROR: {type(exc).__name__}: {exc}"
    finally:
        _ctx.__exit__(None, None, None)
    res.transcript_chars = _transcript_len(messages)
    if wt is not None:
        notes.append(_worktree_summary(wt))
    if notes:
        res.output = (res.output + "\n\n" + "\n".join(notes)).strip()
    res.duration_s = time.perf_counter() - t0
    if ttl > 0 and res.ok and not res.truncated and res.tool_calls == 0:
        _cache_put(_cache_key(subdef, task, model, provider), res, ttl)
    _emit(on_event, {"type": "run_finish", "name": subdef.name, "ok": res.ok,
                     "truncated": res.truncated, "cached": False,
                     "duration_s": res.duration_s})
    return res


def fanout(pool, tools_schema: list, dispatch_fn: Callable,
           default_def: Optional[SubAgentDef] = None,
           jobs: list | tuple = (),
           max_concurrent: int = DEFAULT_MAX_CONCURRENT,
           fail_fast: bool = False,
           on_event=None,
           repo=None) -> list:
    """Run many subagents concurrently (order preserved). Count unbounded, concurrency capped."""
    cap = min(max(int(max_concurrent or DEFAULT_MAX_CONCURRENT), 1), MAX_CONCURRENT_HARD)
    jobs = list(jobs or [])
    if not jobs:
        return []

    def _one(job):
        if fail_fast and failed.is_set():
            return None  # skipped: an earlier job already failed
        name = job.get("name") or (default_def.name if default_def else "")
        subdef = BUILTIN_MAP.get(name, default_def)
        if subdef is None:
            return SubAgentResult(name=name, task=job.get("task", ""),
                                  output=f"ERROR: unknown subagent '{name}'", ok=False)
        r = run_one(pool, tools_schema, dispatch_fn, subdef, job.get("task", ""),
                    max_steps=job.get("max_steps"), max_tokens=job.get("max_tokens"),
                    timeout_s=job.get("timeout_s"), model=job.get("model"),
                    provider=job.get("provider"),
                    isolated=job.get("isolated", False), repo=repo,
                    on_event=on_event, cache_ttl_s=job.get("cache_ttl_s", 0))
        if fail_fast and not r.ok:
            failed.set()
        return r

    failed = threading.Event()
    results: list = []
    with ThreadPoolExecutor(max_workers=min(cap, len(jobs)),
                            thread_name_prefix="chusqui-sub") as ex:
        futures = [ex.submit(_one, job) for job in jobs]
        for i, fut in enumerate(futures):
            try:
                r = fut.result()
            except Exception as exc:
                name = jobs[i].get("name", "?")
                r = SubAgentResult(name=name, task=jobs[i].get("task", ""),
                                   output=f"ERROR: {type(exc).__name__}: {exc}",
                                   ok=False)
            if r is not None:
                results.append(r)
    for r in results:  # protect parent context no matter the fanout size
        if len(r.output) > FANOUT_ITEM_CHARS:
            r.output = r.output[:FANOUT_ITEM_CHARS] + f"…[cut {len(r.output) - FANOUT_ITEM_CHARS} chars]"
    return results


def chain(pool, tools_schema: list, dispatch_fn: Callable,
          jobs: list | tuple = (),
          on_event=None,
          repo=None) -> list:
    """Sequential pipeline: each job sees prior outputs. Halts on first failure."""
    results: list = []
    prior: list = []
    for job in (jobs or []):
        name = job.get("name", "")
        subdef = BUILTIN_MAP.get(name)
        if subdef is None:
            results.append(SubAgentResult(name=name, task=job.get("task", ""),
                                          output=f"ERROR: unknown subagent '{name}'", ok=False))
            break
        task = job.get("task", "")
        if prior:
            context = "\n\n".join(f"Previous step [{n}]:\n{o}"[:FANOUT_ITEM_CHARS]
                                  for n, o in prior)
            task = f"{task}\n\nContext from previous steps:\n{context}"
        r = run_one(pool, tools_schema, dispatch_fn, subdef, task,
                    max_steps=job.get("max_steps"), max_tokens=job.get("max_tokens"),
                    timeout_s=job.get("timeout_s"), model=job.get("model"),
                    provider=job.get("provider"),
                    isolated=job.get("isolated", False), repo=repo,
                    on_event=on_event, cache_ttl_s=job.get("cache_ttl_s", 0))
        results.append(r)
        if not r.ok:
            break
        prior.append((r.name, r.output))
    return results


def subagents_prompt_section() -> str:
    lines = ["You can invoke specialized subagents UNLIMITED times — sequentially or "
             "in parallel batches. Each runs in its own isolated context with only the "
             "tools it needs, and returns a distilled summary. Delegate freely; fan out "
             "3-8 independent subtasks at once, then synthesize. Use the `subagent` tool: "
             "`list` (catalog), `run` (one), `fanout` (many in parallel), `chain` "
             "(sequential pipeline where each step sees prior outputs — worker → "
             "reviewer), `custom` "
             "(define a brand-new subagent type inline and run it — unlimited new types). "
             "Per call you may set model/provider to route cheap work to a smaller model, "
             "and isolated:true to run writers in a throwaway git worktree (shell/code "
             "disabled there, files path-contained, diff appended). "
             "cache_ttl_s reuses pure-reasoning results; tool runs always re-execute. "
             "Every subagent has hard budgets (steps/tokens/time); flat hierarchy only, "
             "subagents cannot spawn subagents.",
             "", "Available subagents:"]
    for d in BUILTIN_DEFS:
        tools = "reasoning only" if d.tools == () else ("all tools" if d.tools is None else ", ".join(d.tools))
        lines.append(f"- {d.name}: {d.description} [tools: {tools}]")
    return "\n".join(lines)


SUBAGENT_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "subagent",
        "description": ("Invoke specialized subagents with isolated context. "
                        "list: show catalog. run: one subagent. fanout: many in parallel. "
                        "custom: define a new subagent type inline and run it."),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string",
                           "enum": ["list", "run", "fanout", "chain", "custom"]},
                "name": {"type": "string",
                         "description": "Builtin subagent name for run"},
                "task": {"type": "string",
                         "description": "Focused task for the subagent"},
                "jobs": {"type": "array",
                         "description": "Fanout/chain jobs: [{name, task, model?, provider?, isolated?}]",
                         "items": {"type": "object"}},
                "fail_fast": {"type": "boolean",
                              "description": "Fanout: stop dispatching after first failure"},
                "cache_ttl_s": {"type": "number",
                                "description": "Cache pure-reasoning results this many seconds (tool runs never cache)"},
                "definition": {"type": "object",
                               "description": "Inline {name, description, instructions, tools?, model?, provider?, isolated?} for custom"},
                "max_steps": {"type": "integer"},
                "max_tokens": {"type": "integer"},
                "timeout_s": {"type": "integer"},
                "model": {"type": "string",
                          "description": "Route this subagent to another model (default inherits)"},
                "provider": {"type": "string",
                             "description": "Route this subagent to another provider (default inherits)"},
                "isolated": {"type": "boolean",
                             "description": "Run writers in a throwaway git worktree (default false)"},
                "max_concurrent": {"type": "integer",
                                   "description": "Fanout parallelism cap (default 8, max 16)"},
            },
            "required": ["action"],
        },
    },
}


def handle_subagent_tool(agent, args: dict) -> ToolResult:
    """Dispatch list/run/fanout/custom for the parent agent. Never raises."""
    try:
        action = (args or {}).get("action", "list")
        if action == "list":
            lines = [f"- {d.name}: {d.description}" for d in BUILTIN_DEFS]
            return ToolResult(success=True, output="Subagents (invoke unlimited times):\n" + "\n".join(lines))
        if action == "run":
            name, task = args.get("name", ""), str(args.get("task", "")).strip()
            subdef = BUILTIN_MAP.get(name)
            if subdef is None:
                return ToolResult(success=False, output="", error=f"Unknown subagent '{name}'. Use action=list.")
            if not task:
                return ToolResult(success=False, output="", error="task is required")
            r = run_one(agent.pool, agent.tools_schema, agent._dispatch_tool, subdef, task,
                        max_steps=args.get("max_steps"), max_tokens=args.get("max_tokens"),
                        timeout_s=args.get("timeout_s"), model=args.get("model"),
                        provider=args.get("provider"),
                        isolated=args.get("isolated", False), repo=os.getcwd(),
                        cache_ttl_s=args.get("cache_ttl_s", 0))
            tag = " [truncated]" if r.truncated else ""
            return ToolResult(success=r.ok, output=f"[{r.name}]{tag} {r.output}",
                              error="" if r.ok else r.output)
        if action == "fanout":
            jobs = args.get("jobs") or []
            if not isinstance(jobs, list) or not jobs:
                return ToolResult(success=False, output="", error="jobs (non-empty list) is required")
            t0 = time.perf_counter()
            results = fanout(agent.pool, agent.tools_schema, agent._dispatch_tool,
                             None, jobs,
                             max_concurrent=args.get("max_concurrent") or DEFAULT_MAX_CONCURRENT,
                             fail_fast=bool(args.get("fail_fast", False)),
                             repo=os.getcwd())
            out = "\n\n".join(f"[{r.name}] {r.output}" for r in results)
            ok = all(r.ok for r in results) and len(results) == len(jobs)
            footer = (f"[fanout: {sum(r.ok for r in results)} ok / {len(jobs)} jobs, "
                      f"{time.perf_counter() - t0:.1f}s wall"
                      f"{'' if len(results) == len(jobs) else ', halted early'}]")
            return ToolResult(success=ok, output=out + "\n\n" + footer,
                              error="" if ok else "some subagents failed")
        if action == "chain":
            jobs = args.get("jobs") or []
            if not isinstance(jobs, list) or not jobs:
                return ToolResult(success=False, output="", error="jobs (non-empty list) is required")
            results = chain(agent.pool, agent.tools_schema, agent._dispatch_tool,
                            jobs, repo=os.getcwd())
            out = "\n\n".join(f"[{r.name}] {r.output}" for r in results)
            ok = all(r.ok for r in results)
            return ToolResult(success=ok, output=out, error="" if ok else "chain halted on failure")
        if action == "custom":
            try:
                subdef = parse_custom(args.get("definition") or {})
            except ValueError as exc:
                return ToolResult(success=False, output="", error=str(exc))
            task = str(args.get("task", "")).strip()
            if not task:
                return ToolResult(success=False, output="", error="task is required")
            r = run_one(agent.pool, agent.tools_schema, agent._dispatch_tool, subdef, task,
                        max_steps=args.get("max_steps"), max_tokens=args.get("max_tokens"),
                        timeout_s=args.get("timeout_s"), model=args.get("model"),
                        provider=args.get("provider"),
                        isolated=args.get("isolated", False), repo=os.getcwd(),
                        cache_ttl_s=args.get("cache_ttl_s", 0))
            return ToolResult(success=r.ok, output=f"[{r.name}] {r.output}",
                              error="" if r.ok else r.output)
        return ToolResult(success=False, output="", error=f"Unknown action '{action}'")
    except Exception as exc:
        return ToolResult(success=False, output="", error=f"{type(exc).__name__}: {exc}")


__all__ = ["BUILTIN_DEFS", "BUILTIN_MAP", "KNOWN_TOOLS", "SubAgentDef", "SubAgentResult",
           "SUBAGENT_TOOL_SCHEMA", "cache_clear", "chain", "fanout", "git_worktree",
           "handle_subagent_tool", "parse_custom", "run_one", "scoped_dispatch",
           "subagents_prompt_section"]
