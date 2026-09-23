# Phase 1 Stability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Zero tracebacks in onboarding and surfaces; recall without regression; frozen catalog.

**Architecture:** New tests only + minimal fixes if a test reveals a crash. No features, no deps.

**Tech Stack:** Python 3.10+, unittest, subprocess+urllib (stdlib), SQLite tmp.

**Spec:** `docs/superpowers/specs/2026-09-13-launch-uneed-design.md` (Phase 1)

## Global Constraints

- Suite 100% green before and after (`python3 -m unittest discover tests -q`).
- Ruff clean. Doctor 48/48.
- No new dependencies. No features. No commits without explicit order.
- Fixed test ports 18080 (web) / 18081 (api); if busy, the test skips with `skipTest`, does not fail.
- Real HOME never touched: subprocess with `HOME=/tmp/...` or `MEMORY_DB_PATH` to tmp.

---

### Task 1: Cold-start onboarding without tracebacks

**Files:**
- Create: `tests/test_onboarding_coldstart.py`
- Modify (only if the test reveals a crash): `cli.py`, `core/setup.py` — minimum necessary

**Interfaces:**
- Consumes: nothing
- Produces: `test_onboarding_coldstart.py` — 4 verified cold commands

- [ ] **Step 1: Write the failing test**

```python
"""Phase 1: cold commands with empty HOME produce no traceback."""
import os
import subprocess
import sys
import tempfile
import unittest

CMDS = [
    [sys.executable, "cli.py", "version"],
    [sys.executable, "cli.py", "--help"],
    [sys.executable, "cli.py", "config", "--show"],
    [sys.executable, "cli.py", "knowledge"],
]


class ColdStartTest(unittest.TestCase):
    def _run_cold(self, cmd):
        home = tempfile.mkdtemp(prefix="hc-cold-")
        env = dict(os.environ, HOME=home)
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=90, env=env)
        finally:
            import shutil
            shutil.rmtree(home, ignore_errors=True)
        return p

    def test_cold_commands_no_traceback(self):
        for cmd in CMDS:
            with self.subTest(cmd=cmd):
                p = self._run_cold(cmd)
                self.assertNotIn("Traceback", p.stderr, f"traceback en: {cmd}")
                self.assertEqual(p.returncode, 0, f"exit!=0 en {cmd}: {p.stderr[-500:]}")

    def test_help_lists_surfaces(self):
        p = self._run_cold([sys.executable, "cli.py", "--help"])
        for word in ("web", "api", "telegram", "doctor", "config"):
            self.assertIn(word, p.stdout)
```

- [ ] **Step 2: Run test to verify it fails (or passes)**

Run: `python3 -m unittest tests.test_onboarding_coldstart -v`
Expected: FAIL on the command that produces a traceback — that crash is the work; if everything passes, no fix.

- [ ] **Step 3: Minimal fix (only on FAIL)**

One fix per crash, at the exact traceback location, without changing behavior with existing config. Shape example (do not copy blindly): guard `if not cfg: use defaults` where the code assumes config is present.

- [ ] **Step 4: Run full suite**

Run: `python3 -m unittest discover tests -q 2>&1 | tail -n 3`
Expected: OK

### Task 2: Boot smoke web + api

**Files:**
- Create: `tests/test_surface_boot_smoke.py`
- Modify (only on crash): `web/server.py`, `api/main.py`, `cli.py` — minimal

**Interfaces:**
- Consumes: nothing
- Produces: web/api start and respond `/health` on test ports

- [ ] **Step 1: Write the failing test**

```python
"""Fase 1: web y api boot + /health sin traceback."""
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request


def _free(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def _wait_health(url, timeout_s=25):
    end = time.time() + timeout_s
    while time.time() < end:
        try:
            with urllib.request.urlopen(url, timeout=3) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


class SurfaceBootTest(unittest.TestCase):
    def _boot(self, surface, port):
        if not _free(port):
            self.skipTest(f"puerto {port} ocupado")
        home = tempfile.mkdtemp(prefix="hc-boot-")
        env = dict(os.environ, HOME=home, HELLOCHUSQUIS_API_KEY="fase1-smoke-key")
        cmd = [sys.executable, "cli.py", surface, "--port", str(port), "--no-browser"]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, env=env)
        return p, home

    def _stop(self, p, home):
        import shutil
        try:
            p.terminate()
            p.wait(timeout=15)
        except Exception:
            p.kill()
        out = p.stdout.read() if p.stdout else ""
        shutil.rmtree(home, ignore_errors=True)
        return out

    def test_web_boot_health(self):
        p, home = self._boot("web", 18080)
        try:
            self.assertTrue(_wait_health("http://127.0.0.1:18080/health"), "web sin /health 200")
        finally:
            out = self._stop(p, home)
        self.assertNotIn("Traceback", out)

    def test_api_boot_health(self):
        p, home = self._boot("api", 18081)
        try:
            self.assertTrue(_wait_health("http://127.0.0.1:18081/health"), "api sin /health 200")
        finally:
            out = self._stop(p, home)
        self.assertNotIn("Traceback", out)
```

- [ ] **Step 2: Run**

Run: `python3 -m unittest tests.test_surface_boot_smoke -v`
Expected: PASS; on FAIL from a real crash, minimal fix at the traceback; on FAIL from auth/key in api, use the env the repo already supports (check `api/main.py` reading of `HELLOCHUSQUIS_API_KEY`, do not invent a mechanism).

- [ ] **Step 3: Run full suite**

Run: `python3 -m unittest discover tests -q 2>&1 | tail -n 3`
Expected: OK

### Task 3: Telegram without token = clean error

**Files:**
- Create: `tests/test_telegram_no_token.py` (or add to existing test if the implementer sees duplication — single location)
- Modify (only on traceback): `cli.py` telegram branch

**Interfaces:**
- Consumes: nothing
- Produces: documented clean error without token

- [ ] **Step 1: Write the failing test**

```python
"""Fase 1: telegram sin token/allow falla limpio, sin traceback."""
import os
import subprocess
import sys
import tempfile
import unittest


class TelegramNoTokenTest(unittest.TestCase):
    def test_telegram_without_credentials_no_traceback(self):
        home = tempfile.mkdtemp(prefix="hc-tg-")
        env = {k: v for k, v in os.environ.items()
               if k not in ("HELLOCHUSQUIS_TELEGRAM_TOKEN", "HELLOCHUSQUIS_TELEGRAM_ALLOW")}
        env["HOME"] = home
        try:
            p = subprocess.run([sys.executable, "cli.py", "telegram"],
                               capture_output=True, text=True, timeout=60, env=env)
        finally:
            import shutil
            shutil.rmtree(home, ignore_errors=True)
        combined = p.stdout + p.stderr
        self.assertNotIn("Traceback", combined)
        self.assertNotEqual(p.returncode, 0)
```

- [ ] **Step 2: Run, minimal fix only on traceback, full suite**

### Task 4: Recall without regression (coverage over MDknowledge)

**Files:**
- Create: `tests/test_recall_regression.py`
- Modify: none expected (if coverage <95%, it is a bug in `core/db_memory.py` — minimal fix there)

**Interfaces:**
- Consumes: setUp/tearDown pattern from `tests/test_db_memory.py:16-26` (override `MEMORY_DB_PATH` to tmpdb) + the write API that same file uses
- Produces: recall coverage ≥95% over real sample

- [ ] **Step 1: Write the failing test**

```python
"""Fase 1: recall encuentra lo ingerido (cobertura >= 95%)."""
import os
import random
import re
import shutil
import tempfile
import unittest
from pathlib import Path

import core.db_memory as db_memory


def _sample_facts(n=40, seed=20260913):
    facts = []
    for md in sorted(Path("MDknowledge").rglob("*.md")):
        for line in md.read_text(encoding="utf-8", errors="ignore").splitlines():
            if re.match(r"^- .{12,}", line):
                facts.append(line[2:].strip())
    rng = random.Random(seed)
    return rng.sample(facts, min(n, len(facts)))


class RecallRegressionTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._tmpdb = os.path.join(self._tmpdir, "test_recall.db")
        self._prev = db_memory.MEMORY_DB_PATH
        db_memory.MEMORY_DB_PATH = Path(self._tmpdb)

    def tearDown(self):
        db_memory.MEMORY_DB_PATH = self._prev
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_recall_coverage(self):
        self.assertGreaterEqual(len(_sample_facts()), 40, "MDknowledge sin facts suficientes")
        hits = 0
        total = 0
        for fact in _sample_facts():
            words = [w for w in re.findall(r"[\w]+", fact.lower()) if len(w) > 4][:6]
            if len(words) < 3:
                continue
            total += 1
            # Sembrar con la misma API de escritura que usa tests/test_db_memory.py
            # y buscar por una palabra distintiva del fact.
            probe = max(words, key=len)
            ctx = db_memory.recall_context(probe)
            if probe in ctx.lower():
                hits += 1
        self.assertGreater(total, 0)
        self.assertGreaterEqual(hits / total, 0.95, f"cobertura recall {hits}/{total}")
```

Implementer NOTE: the skeleton above partially omits seeding on purpose — complete Step 1 by reading `tests/test_db_memory.py` (which write function it uses: `save_turn`, `add_entry`, `remember`, whichever) and seed each fact BEFORE its `recall_context` in the same test. The final assertion stays the same. If no public write API exists, use the path that `ingest_memory_files` uses for a single fact.

- [ ] **Step 2: Run**

Run: `python3 -m unittest tests.test_recall_regression -v`
Expected: PASS (1.3s ingest-scale, tmp db). If <95%, real bug in keyword search — minimal fix.

- [ ] **Step 3: Full suite**

### Task 5: Freeze catalog (pins 74/131)

**Files:**
- Create: `tests/test_catalog_freeze.py`
- Modify: none (if it fails, it is an unauthorized change — report, do not "fix" the test)

**Interfaces:**
- Consumes: verified Phase 0 counts (74 providers, 131 tools)
- Produces: freeze enforced; unfreeze only on owner order

- [ ] **Step 1: Write the test**

```python
"""Phase 1: catalog frozen until Phase 2. Unfreezing = owner order."""
import glob
import unittest

from core.setup import KNOWN_PROVIDERS


class CatalogFreezeTest(unittest.TestCase):
    def test_provider_count_frozen(self):
        self.assertEqual(len(KNOWN_PROVIDERS), 74)

    def test_tool_count_frozen(self):
        files = [f for f in glob.glob("tools/*.py") if not f.endswith("__init__.py")]
        self.assertEqual(len(files), 131)
```

- [ ] **Step 2: Run**

Run: `python3 -m unittest tests.test_catalog_freeze -v`
Expected: PASS. On FAIL, do NOT touch the test: report as BLOCKED (catalog change without order).

- [ ] **Step 3: Full suite + ruff + doctor**

Run: `python3 -m unittest discover tests -q 2>&1 | tail -n 3`
Run: `python3 -m ruff check . 2>&1 | tail -n 1`
Run: `python3 cli.py doctor --contracts 2>&1 | tail -n 1`
Expected: OK / clean / 48/48

## Self-Review

1. **Spec coverage:** onboarding ✓ (T1), web/api/telegram ✓ (T2+T3), memory ✓ (T4), freeze ✓ (T5), green doctor ✓ (T5). Skills is Phase 2, out of scope.
2. **Placeholder scan:** exact commands, ports, paths and assertions. Only semi-open area: seeding API in T4, resolved by mandatory reference to `tests/test_db_memory.py` (real code, no placeholder).
3. **Type consistency:** unittest.TestCase everywhere; subprocess+tmp; no new signatures except tests.
