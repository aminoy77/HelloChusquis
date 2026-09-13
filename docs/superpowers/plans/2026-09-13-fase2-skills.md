# Fase 2 Universal Skills Loader Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Skills universales SKILL.md (estándar `---` frontmatter) cargadas en el registry existente, visibles en prompt y usables vía tool `skill` solo-lectura.

**Architecture:** Extender `core/skills.py` (parse+discover+prompt section), cablear en `core/agent.py` calcando el patrón `subagent` (schema + dispatch + prompt), comando CLI `skills`, 2 ejemplos en `examples/skills/`. Prompt-only: las skills MD exponen `list`/`show`; la ejecución shell con approval queda solo para el registry JSON existente, intacto.

**Tech Stack:** Python 3.10+ stdlib (sin deps). unittest.

**Spec:** `docs/superpowers/specs/2026-09-13-launch-uneed-design.md` (Fase 2)

## Global Constraints

- Suite 100% verde, ruff limpio, doctor 48/48.
- Sin dependencias nuevas. Sin commits sin orden explícita.
- Freeze catálogo Fase 1 SIGUE: `tools/*.py` == 131 (NO crear `tools/skill.py`; el tool `skill` va por schema+dispatch como `subagent`), `KNOWN_PROVIDERS` == 76? NO — == 74. Si un test de freeze falla, BLOCKED, no tocar el test.
- Path traversal bloqueado: solo `*/SKILL.md` directos, sin symlinks fuera, body capado.
- `.agents/` sigue gitignored: discovery lo lee si existe pero nada del repo depende de él.

---

### Task 1: Parse + discover SKILL.md en `core/skills.py`

**Files:**
- Modify: `core/skills.py` (añadir al final; no tocar JSON existente)
- Test: `tests/test_skill_md_loader.py` (nuevo)

**Interfaces:**
- Consumes: clase `Skill` existente
- Produces: `parse_skill_md(text, source="<memory>") -> Skill | None`, `discover_skill_md(dirs) -> int`, `skills_prompt_section() -> str`, consts `SKILL_MD_MAX_CHARS=32768`, `SKILL_MD_MAX_FILES=200`

- [ ] **Step 1: Write the failing test**

```python
"""Fase 2: parse/discover SKILL.md estándar con stdlib."""
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

NOTA: `SkillRegistry(skills_dir=...)` acepta dir (ver `tests/test_skill_registry_execution_security.py:12`). `discover_skill_md` puede ser método (como arriba) o función con registry param — el implementador elige UNA forma y ajusta test+llamadas; `skills_prompt_section` igual (método preferido, espejo de `list_skills`).

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_skill_md_loader -v`
Expected: FAIL (nombres no existen)

- [ ] **Step 3: Minimal implementation** (append en `core/skills.py`, stdlib solo: `re`, `pathlib`)

```python
SKILL_MD_MAX_CHARS = 32768
SKILL_MD_MAX_FILES = 200

def parse_skill_md(text, source="<memory>"):
    """Parse estándar SKILL.md: frontmatter name/description + body. None si inválido."""
    # ... (implementador: regex ^---\n(.*?)\n---\n? cuerpo; name:/^[\w-]+$/ tras sanitizar [^A-Za-z0-9_-]→- ; description no vacía ≤500; body strip capado)
```

Reglas exactas: frontmatter entre primer `---` línea y siguiente `---`; claves `name:`/`description:` (una línea cada una); name sanitizado a `[A-Za-z0-9_-]+` (vacío→None); description strip no vacía; body = resto strip, cap `SKILL_MD_MAX_CHARS`; `Skill(name, description, prompt_template=body, actions=[], requires_approval=True)`.

`discover_skill_md(self, dirs)`: por cada dir existente, `sorted(dir.glob("*/SKILL.md"))` hasta `SKILL_MD_MAX_FILES` total; salta symlinks (`p.is_symlink()`); salta nombres ya registrados (first-wins); `read_text(encoding="utf-8", errors="ignore")` en try/except; cuenta cargados; return count.

`skills_prompt_section(self)`: `"Available skills (use the `skill` tool: `list`, `show`):\n- name: description"` por skill con prompt_template, o `"No skills installed. Drop SKILL.md folders in ~/.hellochusquis/skills/<name>/SKILL.md."` si vacío.

- [ ] **Step 4: Run test + suite**

Run: `python3 -m unittest tests.test_skill_md_loader -v` → PASS
Run: `python3 -m unittest discover tests -q 2>&1 | tail -n 3` → OK

### Task 2: Cablear agent (schema + dispatch + prompt)

**Files:**
- Modify: `core/skills.py` — añadir `SKILL_TOOL_SCHEMA` + `handle_skill_tool(agent, args)` (misma zona que SUBAGENT_TOOL_SCHEMA en `core/subagents.py:557`)
- Modify: `core/agent.py:85` import, `_build_tools_schema` (tras línea 1016 `schema.append(SUBAGENT_TOOL_SCHEMA)`), `_dispatch_tool` (tras líneas 1430-1431), `__init__` (tras línea 1149 bloque knowledge): crear registry, discover, append prompt section
- Test: `tests/test_skill_tool.py` (nuevo)

**Interfaces:**
- Consumes: Task 1 (`discover_skill_md`, `skills_prompt_section`)
- Produces: tool `skill` funcional list/show solo-lectura

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

- [ ] **Step 2: Run** → FAIL (falta `handle_skill_tool`)
- [ ] **Step 3: Implement**

`SKILL_TOOL_SCHEMA` (en `core/skills.py`, espejo de `SUBAGENT_TOOL_SCHEMA`): name `skill`, description `"List and read installed SKILL.md skills. list: catalog (no bodies). show: full skill body by name."`, parameters action enum [list, show] + name string.

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

Agent wiring (4 ediciones en `core/agent.py`):
1. `from core.skills import SKILL_TOOL_SCHEMA, discover_skill_md...` — mejor: `from core import skills as skills_module` y usar `skills_module.*` (evita choques de nombres; `core/registry.py` ya tiene `get_registry` distinto).
2. En `_build_tools_schema`, tras `schema.append(SUBAGENT_TOOL_SCHEMA)`: `schema.append(skills_module.SKILL_TOOL_SCHEMA)`.
3. En `_dispatch_tool`, tras bloque subagent: `if name == "skill": return skills_module.handle_skill_tool(self, args)`.
4. En `__init__` tras bloque knowledge (línea ~1149): `self.skills = skills_module.get_registry(); skills_module... discover en [~/.hellochusquis/skills, <repo>/.agents/skills] BEST-EFFORT try/except; self.system_prompt += "\n\n" + self.skills.skills_prompt_section()` — solo si hay skills con body? NO: siempre append (sección corta avisa dónde instalar). Repo dir = `Path(__file__).resolve().parent.parent / ".agents" / "skills"`.

- [ ] **Step 4: Run test → PASS, suite OK**

### Task 3: CLI `skills list|show`

**Files:**
- Modify: `cli.py` — `KNOWN_COMMANDS` + rama comando (mirar cómo se despacha `knowledge`/`memory`, reusar ese shape)
- Test: `tests/test_cli_skills.py` (subprocess frío como Task 1 Fase 1: `skills list` con HOME tmp → exit 0, sin Traceback, contiene "alpha"? NO — HOME tmp no tiene skills; asertar exit 0 + sin Traceback + menciona `~/.hellochusquis/skills`)

**Interfaces:**
- Consumes: Task 1–2
- Produces: `hellochusquis skills list|show <name>`

- [ ] **Step 1-3:** test → FAIL → implement (list usa registry+discover mismos dirs que agent; show imprime body capado 8000) → PASS + suite OK. Detalle de despacho CLI lo lee el implementador en `cli.py` (rama `knowledge`).

### Task 4: 2 skills ejemplo + README

**Files:**
- Create: `examples/skills/code-review/SKILL.md`, `examples/skills/standup-notes/SKILL.md` (cortas, reales, sin shell)
- Modify: `README.md` — snippet ≤15 líneas (qué es, dónde instalar, `skills list`, link uneed? NO — solo docs)
- Test: ninguno nuevo; verificación = `parse_skill_md` las acepta (one-liner en reporte, no test)

**Interfaces:**
- Consumes: Task 1
- Produces: ejemplos copiables a `~/.hellochusquis/skills/`

- [ ] **Step 1:** escribir los 2 ficheros (cada uno: frontmatter name/description + body 10-25 líneas útiles de verdad).
- [ ] **Step 2:** README snippet + `python3 -c` que parsea ambos con `parse_skill_md` OK (evidencia en reporte).

### Task 5: Cierre (freeze + verde global)

**Files:** ninguno

- [ ] **Step 1: Run todo**

Run: `python3 -m unittest discover tests -q 2>&1 | tail -n 3` → OK (esperado 407 + ~7 nuevos)
Run: `python3 -m ruff check . 2>&1 | tail -n 1` → clean
Run: `python3 cli.py doctor --contracts 2>&1 | tail -n 1` → 48/48 (los contracts chequean `run` importable por módulo — NO se añadió módulo tools/, así que nada cambia; si doctor lista tools y exige `skill`, reportar BLOCKED, no parchear doctor)
Run: `python3 -m unittest tests.test_catalog_freeze tests.test_version_consistency -v 2>&1 | tail -n 4` → freeze holds

## Self-Review

1. **Spec coverage:** loader ✓ (T1), discover+prompt ✓ (T1–T2), tool bridge ✓ (T2), CLI ✓ (T3), docs+2 demos ✓ (T4), freeze 1-dic n/a aún pero pins intactos ✓ (T5).
2. **Placeholder scan:** firmas, paths, enums y consts exactos. T3 deja shape CLI al implementador con referencia obligada (rama `knowledge` real).
3. **Type consistency:** `Skill` existente reusado; `ToolResult` de `tools.base`; prompts section string.
