# Fase 3 Packaging (early) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Higiene de release + assets launch (GIF demo, badges reales, sitemap) sin features.

**Architecture:** Ediciones estáticas + 1 test higiene + 1 GIF generado. Cero código runtime.

**Tech Stack:** unittest, ffmpeg en /tmp (PATH=/tmp:$PATH), git.

**Spec:** `docs/superpowers/specs/2026-09-13-launch-uneed-design.md` (Fase 3)

## Global Constraints

- Suite verde, ruff limpio, doctor 48/48. Sin deps, sin features, sin commits sin orden.
- Freeze holds: tools==131, providers==74.
- `hellochusquis-landing.html` raíz se BORRA (duplicado stale, cero referencias reales — verificado 2026-09-13).
- GIF ≤6MB para GitHub README.

---

### Task 1: Batch diferidos (gitignore, badge, sitemap, landing stale, changelog)

**Files:**
- Modify: `.gitignore` (append `dist/`), `README.md:13` (badge), `sitemap.xml` (lastmod), `CHANGELOG.md` (mover bloque `## 5.4` encima de `## 5.3`)
- Delete: `hellochusquis-landing.html`
- Test: `tests/test_packaging_hygiene.py` (nuevo)

**Interfaces:**
- Consumes: conteo tests real (187? NO — medir con `python3 -m unittest discover tests -q | grep Ran` antes de editar badge)
- Produces: higiene verificada por test

- [ ] **Step 1: Write the failing test**

```python
"""Fase 3: higiene packaging/launch estática."""
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


class PackagingHygieneTest(unittest.TestCase):
    def test_dist_ignored(self):
        content = Path(".gitignore").read_text()
        self.assertIn("dist/", content.splitlines())

    def test_sitemap_valid(self):
        tree = ET.parse("sitemap.xml")
        locs = [e.text for e in tree.getroot().iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
        self.assertIn("https://hellochusquis.dev/", locs)

    def test_no_stale_root_landing(self):
        self.assertFalse(Path("hellochusquis-landing.html").exists())

    def test_changelog_newest_first(self):
        import re
        versions = re.findall(r"^## (\d+\.\d+)", Path("CHANGELOG.md").read_text(), re.M)
        self.assertGreaterEqual(len(versions), 2)
        self.assertEqual(versions[0], "5.4")
```

- [ ] **Step 2: Run** → FAIL (4 fallospequeños esperados; si badge... el badge NO va en test — ver Step 3)
- [ ] **Step 3: Ediciones**
  - `.gitignore`: append `dist/` (verificar `build/` ya está).
  - Badge: medir `Ran N` real y poner `tests-N passing` en `README.md:13`; añadir badge PyPI real: `[![PyPI](https://img.shields.io/pypi/v/hellochusquis.svg)](https://pypi.org/project/hellochusquis/)` tras el badge Tests.
  - `sitemap.xml`: lastmod → fecha hoy ISO.
  - `rm hellochusquis-landing.html`.
  - CHANGELOG: mover bloque `## 5.4 — ...` completo encima de `## 5.3`, sin tocar texto.
- [ ] **Step 4: Run test → PASS; `tests.test_version_consistency` → PASS; suite OK**

### Task 2: GIF demo para README/uneed

**Files:**
- Create: `docs/assets/demo.gif` (≤6MB)
- Modify: `README.md` (embed bajo el banner, 1 línea)

**Interfaces:**
- Consumes: `videos/hellochusquis-ui-60s/renders/ui-60s.mp4`
- Produces: loop corto640-960px, 8-10s, primeros segundos

- [ ] **Step 1: Generar** (ffmpeg vive en /tmp)

Run: `PATH=/tmp:$PATH ffmpeg -y -t 10 -i videos/hellochusquis-ui-60s/renders/ui-60s.mp4 -vf "fps=12,scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse" docs/assets/demo.gif 2>&1 | tail -n 2`
- [ ] **Step 2: Verificar peso**

Run: `ls -lh docs/assets/demo.gif; PATH=/tmp:$PATH ffprobe -v error -show_entries format=duration -of csv=p=0 docs/assets/demo.gif`
Expected: ≤6MB, ~10s. Si >6MB: bajar a `scale=720`, fps=10, re-run (una vez; si sigue, ` -t 8`).
- [ ] **Step 3: Embed README** (1 línea bajo banner): `![Demo: 60s UI tour](docs/assets/demo.gif)` — alt real.
- [ ] **Step 4: Sin test** (binario; evidencia del Step 2 en reporte basta).

### Task 3: Cierre verde global

**Files:** ninguno

- [ ] **Step 1: Run todo**

Run: `python3 -m unittest discover tests -q 2>&1 | tail -n 3` → OK
Run: `python3 -m ruff check . 2>&1 | tail -n 1` → clean
Run: `python3 cli.py doctor --contracts 2>&1 | tail -n 1` → 48/48
Run: `python3 -m unittest tests.test_catalog_freeze tests.test_version_consistency tests.test_packaging_hygiene -v 2>&1 | tail -n 4` → OK
Run: `python3 -m build 2>&1 | tail -n 1 && python3 -m twine check dist/* 2>&1 | tail -n 2 && rm -rf dist build hellochusquis.egg-info` → PASSED x2 (SIN upload)

## Self-Review

1. **Spec coverage:** freeze ✓ (diferidos absorbidos), README ✓ (GIF+badges), SEO ✓ (sitemap), dry-run PyPI ✓ (T3), Deal/uneed ⏳ (requiere owner, fuera).
2. **Placeholder scan:** comandos, líneas, límites exactos. Badge N se mide, no se inventa.
3. **Type consistency:** solo estáticos + 1 test; sin firmas nuevas.
