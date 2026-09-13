# Fase 1 Estabilidad Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cero tracebacks en onboarding y superficies; recall sin regresión; catálogo congelado.

**Architecture:** Solo tests nuevos + fixes mínimos si un test revela crash. Sin features, sin deps.

**Tech Stack:** Python 3.10+, unittest, subprocess+urllib (stdlib), SQLite tmp.

**Spec:** `docs/superpowers/specs/2026-09-13-launch-uneed-design.md` (Fase 1)

## Global Constraints

- Suite 100% verde antes y después (`python3 -m unittest discover tests -q`).
- Ruff limpio. Doctor 48/48.
- Sin dependencias nuevas. Sin features. Sin commits sin orden explícita.
- Puertos de test fijos 18080 (web) / 18081 (api); si ocupados, el test salta con `skipTest`, no falla.
- HOME real jamás tocado: subprocess con `HOME=/tmp/...` o `MEMORY_DB_PATH` a tmp.

---

### Task 1: Cold-start onboarding sin tracebacks

**Files:**
- Create: `tests/test_onboarding_coldstart.py`
- Modify (solo si el test revela crash): `cli.py`, `core/setup.py` — mínimo necesario

**Interfaces:**
- Consumes: nada
- Produces: `test_onboarding_coldstart.py` — 4 comandos fríos verificados

- [ ] **Step 1: Write the failing test**

```python
"""Fase 1: comandos fríos con HOME vacío no hacen traceback."""
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

- [ ] **Step 2: Run test to verify it fails (o pasa)**

Run: `python3 -m unittest tests.test_onboarding_coldstart -v`
Expected: FAIL en el comando que haga traceback — ese crash es el trabajo; si todo pasa, no hay fix.

- [ ] **Step 3: Fix mínimo (solo si hay FAIL)**

Un fix por crash, en el punto exacto del traceback, sin cambiar comportamiento con config existente. Ejemplo de forma (no copiar a ciegas): guardar `if not cfg: usar defaults` donde el código asume config presente.

- [ ] **Step 4: Run suite completa**

Run: `python3 -m unittest discover tests -q 2>&1 | tail -n 3`
Expected: OK

### Task 2: Boot smoke web + api

**Files:**
- Create: `tests/test_surface_boot_smoke.py`
- Modify (solo si hay crash): `web/server.py`, `api/main.py`, `cli.py` — mínimo

**Interfaces:**
- Consumes: nada
- Produces: web/api arrancan y responden `/health` en puertos de test

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
Expected: PASS; si FAIL por crash real, fix mínimo en el traceback; si FAIL por auth/key en api, usar la env que el repo ya soporte (mirar `api/main.py` lectura de `HELLOCHUSQUIS_API_KEY`, no inventar mecanismo).

- [ ] **Step 3: Run suite completa**

Run: `python3 -m unittest discover tests -q 2>&1 | tail -n 3`
Expected: OK

### Task 3: Telegram sin token = error limpio

**Files:**
- Create: `tests/test_telegram_no_token.py` (o añadir a test existente si el implementador ve duplicación — una sola ubicación)
- Modify (solo si hay traceback): `cli.py` rama telegram

**Interfaces:**
- Consumes: nada
- Produces: error limpio documentado sin token

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

- [ ] **Step 2: Run, fix mínimo solo si hay traceback, suite completa**

### Task 4: Recall sin regresión (cobertura sobre MDknowledge)

**Files:**
- Create: `tests/test_recall_regression.py`
- Modify: ninguno esperado (si cobertura <95%, es bug de `core/db_memory.py` — fix mínimo ahí)

**Interfaces:**
- Consumes: patrón setUp/tearDown de `tests/test_db_memory.py:16-26` (override `MEMORY_DB_PATH` a tmpdb) + la API de escritura que ese mismo fichero usa
- Produces: cobertura recall ≥95% sobre muestra real

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

NOTA implementador: el esqueleto de arriba omite la siembra a propósito parcial — completa el Step 1 leyendo `tests/test_db_memory.py` (qué función de escritura usa: `save_turn`, `add_entry`, `remember`, la que sea) y siembra cada fact ANTES de su `recall_context` en el mismo test. La aserción final queda igual. Si la API de escritura no existe pública, usa el path que `ingest_memory_files` usa para un fact individual.

- [ ] **Step 2: Run**

Run: `python3 -m unittest tests.test_recall_regression -v`
Expected: PASS (1.3s ingest-scale, tmp db). Si <95%, bug real en keyword search — fix mínimo.

- [ ] **Step 3: Suite completa**

### Task 5: Congelar catálogo (pins 74/131)

**Files:**
- Create: `tests/test_catalog_freeze.py`
- Modify: ninguno (si falla, es cambio no autorizado — reportar, no "arreglar" el test)

**Interfaces:**
- Consumes: conteos verificados Fase 0 (74 providers, 131 tools)
- Produces: freeze enforced; descongelar solo con orden owner

- [ ] **Step 1: Write the test**

```python
"""Fase 1: catálogo congelado hasta Fase 2. Descongelar = orden owner."""
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
Expected: PASS. Si FAIL, NO tocar el test: reportar como BLOCKED (cambio de catálogo sin orden).

- [ ] **Step 3: Suite completa + ruff + doctor**

Run: `python3 -m unittest discover tests -q 2>&1 | tail -n 3`
Run: `python3 -m ruff check . 2>&1 | tail -n 1`
Run: `python3 cli.py doctor --contracts 2>&1 | tail -n 1`
Expected: OK / clean / 48/48

## Self-Review

1. **Spec coverage:** onboarding ✓ (T1), web/api/telegram ✓ (T2+T3), memoria ✓ (T4), freeze ✓ (T5), doctor verde ✓ (T5). Skills es Fase 2, fuera.
2. **Placeholder scan:** comandos, puertos, paths y aserciones exactos. Única zona semi-abierta: API de siembra en T4, resuelta por referencia obligada a `tests/test_db_memory.py` (código real, no placeholder).
3. **Type consistency:** unittest.TestCase en todos; subprocess+tmp; sin firmas nuevas salvo tests.
