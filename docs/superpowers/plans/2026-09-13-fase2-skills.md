# Phase 2 Universal Skills Loader Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Universal SKILL.md skills (standard `---` frontmatter) loaded into the existing registry, visible in prompt and usable via read-only `skill` tool.

**Architecture:** Extend `core/skills.py` (parse+discover+prompt section), wire into `core/agent.py` copying the `subagent` pattern (schema + dispatch + prompt), `skills` CLI command, 2 examples in `examples/skills/`. Prompt-only: MD skills expose `list`/`show`; shell execution with approval stays only for the existing JSON registry, untouched.

**Tech Stack:** Python 3.10+ stdlib (no deps). unittest.

**Spec:** `docs/superpowers/specs/2026-09-13-launch-uneed-design.md` (Phase 2)

## Global Constraints

- Suite 100% green, ruff clean, doctor 48/48.
- No new dependencies. No commits without explicit order.
- Phase 1 catalog freeze STILL HOLDS: `tools/*.py` == 131 (DO NOT create `tools/skill.py`; the `skill` tool goes via schema+dispatch like `subagent`), `KNOWN_PROVIDERS` == 76? NO — == 74. If a freeze test fails, BLOCKED, do not touch the test.
- Path traversal blocked: only direct `*/SKILL.md`, no symlinks outside, capped body.
- `.agents/` stays gitignored: discovery reads it if present but nothing in the repo depends on it.

---

### Task 1: Parse + discover SKILL.md in `core/skills.py`

**Files:**
- Modify: `core/skills.py` (append at end; do not touch existing JSON)
- Test: `tests/test_skill_md_loader.py` (new)

**Interfaces:**
- Consumes: existing `Skill` class
- Produces: `parse_skill_md(text, source="<memory>") -> Skill | None`, `discover_skill_md(dirs) -> int`, `skills_prompt_section() -> str`, consts `SKILL_MD_MAX_CHARS=32768`, `SKILL_MD_MAX_FILES=200`

- [ ] **Step 1: Write the failing test**

```python
"""Phase 2: standard SKILL.md parse/discover with stdlib."""
import unittest
from pathlib import Path
import tempfile

from core.skills import (
    SkillRegistry, discover_skill_md, parse_skill_md, skills_prompt_section,
)


class SkillMdTest(unittest.TestCase):
    def test_parse_valid(self):
        text = "---\nname: code-review\ndescription: Reviews code\n---\n\n# Code review\nBe strict.\n"
        skill = parse_skill_md(text, source="test")
        self.assertIsNotNone(skill)
        self.assertEqual(skill.name, "code-review")
        self.assertEqual(skill.description, "Reviews code")
        self.assertIn("Be strict", skill.prompt_template)
        self.assertEqual(skill.actions, [])

    def test_parse_invalid(self):
        self.assertIsNone(parse_skill_md("no frontmatter here"))
        self.assertIsNone(parse_skill_md("---\nname: x\n---\n"))  # sin description
        self.assertIsNone(parse_skill_md("---\ndescription: y\n---\nbody"))  # sin name

    def test_name_sanitized(self):
        text = "---\nname: ../../evil\ndescription: d\n---\nbody\n"
        skill = parse_skill_md(text)
        self.assertIsNotNone(skill)
        self.assertNotIn("/", skill.name)
        self.assertNotIn(".", skill.name.replace("-", ""))

    def test_discover_and_section(self):
        tmp = Path(tempfile.mkdtemp(prefix="hc-skills-"))
        (tmp / "alpha").mkdir()
        (tmp / "alpha" / "SKILL.md").write_text("---\nname: alpha\ndescription: A skill\n---\nBody A\n")
        (tmp / "broken").mkdir()
        (tmp / "broken" / "SKILL.md").write_text("garbage")
        reg = SkillRegistry(skills_dir=str(tmp / "nonexistent-json"))
        n = reg.discover_skill_md([str(tmp)])
        self.assertEqual(n, 1)
        self.assertIn("alpha", [s["name"] for s in reg.list_skills()])
        section = reg.skills_prompt_section()
        self.assertIn("alpha", section)
```

NOTE: `SkillRegistry(skills_dir=...)` accepts a dir (see `tests/test_skill_registry_execution_security.py:12`). `discover_skill_md` can be a method (as above) or a function with a registry param — the implementer picks ONE form and adjusts test+calls; `skills_prompt_section` likewise (method preferred, mirror of `list_skills`).

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_skill_md_loader -v`
Expected: FAIL (names do not exist yet)

- [ ] **Step 3: Minimal implementation** (append in `core/skills.py`, stdlib only: `re`, `pathlib`)

```python
SKILL_MD_MAX_CHARS = 32768
SKILL_MD_MAX_FILES = 200

def parse_skill_md(text, source="<memory>"):
    """Standard SKILL.md parse: name/description frontmatter + body. None if invalid."""
    # ... (implementer: regex ^---\n(.*?)\n---\n? body; name:/^[\w-]+$/ after sanitizing [^A-Za-z0-9_-]→- ; non-empty description ≤500; stripped body capped)
```

Exact rules: frontmatter between first `---` line and next `---`; `name:`/`description:` keys (one line each); name sanitized to `[A-Za-z0-9_-]+` (empty→None); description stripped non-empty; body = remaining stripped, capped at `SKILL_MD_MAX_CHARS`; `Skill(name, description, prompt_template=body, actions=[], requires_approval=True)`.

`discover_skill_md(self, dirs)`: for each existing dir, `sorted(dir.glob("*/SKILL.md"))` up to `SKILL_MD_MAX_FILES` total; skip symlinks (`p.is_symlink()`); skip already-registered names (first-wins); `read_text(encoding="utf-8", errors="ignore")` in try/except; count loaded; return count.

`skills_prompt_section(self)`: `"Available skills (use the `skill` tool: `list`, `show`):\n- name: description"` per skill with prompt_template, or `"No skills installed. Drop SKILL.md folders in ~/.hellochusquis/skills/<name>/SKILL.md."` if empty.

- [ ] **Step 4: Run test + suite**

Run: `python3 -m unittest tests.test_skill_md_loader -v` → PASS
Run: `python3 -m unittest discover tests -q 2>&1 | tail -n 3` → OK

### Task 2: Wire agent (schema + dispatch + prompt)

**Files:**
- Modify: `core/skills.py` — add `SKILL_TOOL_SCHEMA` + `handle_skill_tool(agent, args)` (same area as SUBAGENT_TOOL_SCHEMA in `core/subagents.py:557`)
- Modify: `core/agent.py:85` import, `_build_tools_schema` (after line 1016 `schema.append(SUBAGENT_TOOL_SCHEMA)`), `_dispatch_tool` (after lines 1430-1431), `__init__` (after line 1149 knowledge block): create registry, discover, append prompt section
- Test: `tests/test_skill_tool.py` (new)

**Interfaces:**
- Consumes: Task 1 (`discover_skill_md`, `skills_prompt_section`)
- Produces: functional read-only `skill` tool with list/show

- [ ] **Step 1: Write the failing test**

```python
"""Fase 2: tool skill list/show + prompt section cableada."""
import unittest
from pathlib import Path
import tempfile

from core.skills import SkillRegistry


class FakeAgent:
    def __init__(self, registry):
        self.skills = registry


class SkillToolTest(unittest.TestCase):
    def _agent(self):
        from core.skills import handle_skill_tool
        tmp = Path(tempfile.mkdtemp(prefix="hc-skilltool-"))
        (tmp / "alpha").mkdir()
        (tmp / "alpha" / "SKILL.md").write_text("---\nname: alpha\ndescription: A skill\n---\nBody A\n")
        reg = SkillRegistry(skills_dir=str(tmp / "no-json"))
        reg.discover_skill_md([str(tmp)])
        return FakeAgent(reg), handle_skill_tool

    def test_list_hides_bodies(self):
        agent, handle = self._agent()
        res = handle(agent, {"action": "list"})
        self.assertTrue(res.success)
        self.assertIn("alpha", res.output)
        self.assertNotIn("Body A", res.output)

    def test_show_returns_body(self):
        agent, handle = self._agent()
        res = handle(agent, {"action": "show", "name": "alpha"})
        self.assertTrue(res.success)
        self.assertIn("Body A", res.output)

    def test_show_missing(self):
        agent, handle = self._agent()
        res = handle(agent, {"action": "show", "name": "nope"})
        self.assertFalse(res.success)
```

- [ ] **Step 2: Run** → FAIL (missing `handle_skill_tool`)
- [ ] **Step 3: Implement**

`SKILL_TOOL_SCHEMA` (in `core/skills.py`, mirror of `SUBAGENT_TOOL_SCHEMA`): name `skill`, description `"List and read installed SKILL.md skills. list: catalog (no bodies). show: full skill body by name."`, parameters action enum [list, show] + name string.

```python
def handle_skill_tool(agent, args):
    from tools.base import ToolResult
    action = (args.get("action") or "list").lower()
    if action == "list":
        items = agent.skills.list_skills()
        lines = [f"- {s['name']}: {s.get('description','')}" for s in items] or ["(no skills installed)"]
        return ToolResult(success=True, output="\n".join(lines))
    if action == "show":
        skill = agent.skills.skills.get(args.get("name", ""))
        if skill is None or not skill.prompt_template:
            return ToolResult(success=False, output="", error=f"Skill not found: {args.get('name','')}")
        return ToolResult(success=True, output=skill.prompt_template[:8000])
    return ToolResult(success=False, output="", error=f"Unknown skill action: {action}")
```

Agent wiring (4 edits in `core/agent.py`):
1. `from core.skills import SKILL_TOOL_SCHEMA, discover_skill_md...` — better: `from core import skills as skills_module` and use `skills_module.*` (avoids name clashes; `core/registry.py` already has a different `get_registry`).
2. In `_build_tools_schema`, after `schema.append(SUBAGENT_TOOL_SCHEMA)`: `schema.append(skills_module.SKILL_TOOL_SCHEMA)`.
3. In `_dispatch_tool`, after subagent block: `if name == "skill": return skills_module.handle_skill_tool(self, args)`.
4. In `__init__` after knowledge block (line ~1149): `self.skills = skills_module.get_registry(); skills_module... discover in [~/.hellochusquis/skills, <repo>/.agents/skills] BEST-EFFORT try/except; self.system_prompt += "\n\n" + self.skills.skills_prompt_section()` — only if there are skills with body? NO: always append (short section tells where to install). Repo dir = `Path(__file__).resolve().parent.parent / ".agents" / "skills"`.

- [ ] **Step 4: Run test → PASS, suite OK**

### Task 3: CLI `skills list|show`

**Files:**
- Modify: `cli.py` — `KNOWN_COMMANDS` + command branch (see how `knowledge`/`memory` is dispatched, reuse that shape)
- Test: `tests/test_cli_skills.py` (cold subprocess like Phase 1 Task 1: `skills list` with tmp HOME → exit 0, no Traceback, contains "alpha"? NO — tmp HOME has no skills; assert exit 0 + no Traceback + mentions `~/.hellochusquis/skills`)

**Interfaces:**
- Consumes: Tasks 1–2
- Produces: `hellochusquis skills list|show <name>`

- [ ] **Step 1-3:** test → FAIL → implement (list uses registry+discover same dirs as agent; show prints capped 8000 body) → PASS + suite OK. CLI dispatch detail is read by the implementer in `cli.py` (`knowledge` branch).

### Task 4: 2 example skills + README

**Files:**
- Create: `examples/skills/code-review/SKILL.md`, `examples/skills/standup-notes/SKILL.md` (short, real, no shell)
- Modify: `README.md` — snippet ≤15 lines (what it is, where to install, `skills list`, uneed link? NO — docs only)
- Test: no new tests; verification = `parse_skill_md` accepts them (one-liner in report, not a test)

**Interfaces:**
- Consumes: Task 1
- Produces: examples copyable to `~/.hellochusquis/skills/`

- [ ] **Step 1:** write the 2 files (each: frontmatter name/description + 10-25 lines of genuinely useful body).
- [ ] **Step 2:** README snippet + `python3 -c` parsing both with `parse_skill_md` OK (evidence in report).

### Task 5: Closeout (freeze + global green)

**Files:** none

- [ ] **Step 1: Run everything**

Run: `python3 -m unittest discover tests -q 2>&1 | tail -n 3` → OK (expected 407 + ~7 new)
Run: `python3 -m ruff check . 2>&1 | tail -n 1` → clean
Run: `python3 cli.py doctor --contracts 2>&1 | tail -n 1` → 48/48 (contracts check importable `run` per module — NO tools/ module was added, so nothing changes; if doctor lists tools and requires `skill`, report BLOCKED, do not patch doctor)
Run: `python3 -m unittest tests.test_catalog_freeze tests.test_version_consistency -v 2>&1 | tail -n 4` → freeze holds

## Self-Review

1. **Spec coverage:** loader ✓ (T1), discover+prompt ✓ (T1–T2), tool bridge ✓ (T2), CLI ✓ (T3), docs+2 demos ✓ (T4), Dec-1 freeze n/a yet but pins intact ✓ (T5).
2. **Placeholder scan:** signatures, paths, enums and consts exact. T3 leaves CLI shape to implementer with required reference (real `knowledge` branch).
3. **Type consistency:** existing `Skill` reused; `ToolResult` from `tools.base`; prompts section string.

(End of file - total 237 lines)
