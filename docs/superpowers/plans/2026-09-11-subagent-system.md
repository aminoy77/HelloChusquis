# Subagent System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Main agent invokes unlimited specialized subagents (isolated context, tool allowlists, hard budgets) via one `subagent` tool with list/run/fanout/custom actions.

**Architecture:** `core/subagents.py` holds 12 curated defs + sync runner reusing parent pool/schema/dispatch (in-process threads, no new deps); `agents/<name>/AGENT.md` documents each; `agent.py` gains schema entry + dispatch branch + prompt section.

**Tech Stack:** Python stdlib (`concurrent.futures`, `time`), existing `ProviderPool.chat_with_retry`, `ToolResult`.

**Spec:** user request 2026-09-11 (unlimited invocation, ~25MB RAM each, AGENT.md per agent, zero errors) + research (fan-out/fan-in, budgets, harness allowlists, flat hierarchy).

## Global Constraints

- No new dependencies, stdlib only.
- Real tool names only (49 in `core/agent.py` schema).
- RSS caps unenforceable in-process: enforce transcript/step/time/concurrency budgets instead, documented.
- Fanout truncates each result to 1500 chars to protect parent context.

---

### Task 1: Failing tests

**Files:**
- Create: `tests/test_subagents.py`

**Interfaces:**
- Consumes: `core.subagents` (does not exist yet)
- Produces: contract for Task 2 (`BUILTIN_DEFS`, `parse_custom`, `run_one`, `fanout`, `handle_subagent_tool`, `subagents_prompt_section`, `SUBAGENT_TOOL_SCHEMA`, `SubAgentResult`)

- [ ] **Step 1: Write `tests/test_subagents.py`** with FakePool/FakeDispatch covering: 12 defs valid + tools ⊆ real schema names from `core.agent._build_tools_schema([])`; `run_one` returns output; disallowed tool blocked; tiny `max_tokens` truncates; `fanout` peak concurrency ≤ cap; `custom` rejects bad name/unknown tool; prompt section lists all names.

- [ ] **Step 2: Run, expect FAIL** (`ModuleNotFoundError: core.subagents`).

### Task 2: `core/subagents.py`

**Files:**
- Create: `core/subagents.py`

**Interfaces:**
- Consumes: parent `pool.chat_with_retry(messages, tools=...)`, `tools_schema` list, `dispatch_fn(name, args) -> ToolResult`
- Produces: names above for Tasks 3–4.

- [ ] **Step 1: Implement** `SubAgentDef`, 12 `BUILTIN_DEFS` (explorer/planner/researcher/coder/reviewer/debugger/tester/docs-writer/data-analyst/devops/security-auditor/integrator), `run_one` (sync loop, allowlist enforced in harness, transcript/step/timeout budgets), `fanout` (ThreadPoolExecutor, cap 8), `parse_custom`, `handle_subagent_tool` (list/run/fanout/custom), `subagents_prompt_section`, `SUBAGENT_TOOL_SCHEMA`.
- [ ] **Step 2: Run tests, expect PASS.**

### Task 3: AGENT.md per subagent

**Files:**
- Create: `agents/<name>/AGENT.md` × 12 (role, invoke-when, inputs, outputs, tools, stop conditions).

- [ ] **Step 1: Write the 12 files**, names/descriptions/tools identical to Task 2 defs.
- [ ] **Step 2: Grep-check** every `tools:` entry against the 49 real names.

### Task 4: Wire `core/agent.py`

**Files:**
- Modify: `core/agent.py` (import, `_build_tools_schema` += subagent entry, `_dispatch_tool` += branch, `__init__` += prompt section).

- [ ] **Step 1: Apply 4 edits**, reusing `SUBAGENT_TOOL_SCHEMA` / `handle_subagent_tool` / `subagents_prompt_section` (no duplicated text).
- [ ] **Step 2: Run tests + smoke** (`handle_subagent_tool` list action with stub agent).

### Task 5: Verify + changelog

**Files:**
- Modify: `CHANGELOG.md` (Unreleased entry).

- [ ] **Step 1: `py_compile`, full new-test file, related suite** (`-k "subagent or web or server"`).
- [ ] **Step 2: Commit.**

---

### Task 6 (iteration 2): Model routing + worktree isolation + flat guard

**Files:**
- Modify: `core/subagents.py` (def fields, `scoped_dispatch`, `git_worktree`, `run_one`/`fanout`/`handle` params, schema, prompt), `tests/test_subagents.py`, 3 AGENT.md files, `CHANGELOG.md`.

- [ ] Routing: `model`/`provider` per call threaded to `pool.chat_with_retry`; test asserts kwargs.
- [ ] Flat guard: `subagent` tool calls inside `run_one` blocked in harness; test asserts never dispatched.
- [ ] Isolation: `git_worktree` ctx manager + `scoped_dispatch` path guard (shell/code blocked); `isolated` flag on defs/calls; diff appended; tests cover guard + real worktree create/clean.
- [ ] Docs: schema properties, prompt lines, AGENT.md model/isolation lines, changelog.
