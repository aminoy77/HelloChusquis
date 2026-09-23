# Phase 3 Packaging (early) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Release hygiene + launch assets (demo GIF, real badges, sitemap) with no features.

**Architecture:** Static edits + 1 hygiene test + 1 generated GIF. Zero runtime code.

**Tech Stack:** unittest, ffmpeg in /tmp (PATH=/tmp:$PATH), git.

**Spec:** `docs/superpowers/specs/2026-09-13-launch-uneed-design.md` (Phase 3)

## Global Constraints

- Green suite, clean ruff, doctor 48/48. No deps, no features, no commits without order.
- Freeze holds: tools==131, providers==74.
- Root `hellochusquis-landing.html` gets DELETED (stale duplicate, zero real references — verified 2026-09-13).
- GIF ≤6MB for GitHub README.

---

### Task 1: Deferred batch (gitignore, badge, sitemap, stale landing, changelog)

**Files:**
- Modify: `.gitignore` (append `dist/`), `README.md:13` (badge), `sitemap.xml` (lastmod), `CHANGELOG.md` (move `## 5.4` block above `## 5.3`)
- Delete: `hellochusquis-landing.html`
- Test: `tests/test_packaging_hygiene.py` (new)

**Interfaces:**
- Consumes: real test count (187? NO — measure with `python3 -m unittest discover tests -q | grep Ran` before editing badge)
- Produces: test-verified hygiene

- [ ] **Step 1: Write the failing test**

```python
"""Phase 3: static packaging/launch hygiene."""
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

- [ ] **Step 2: Run** → FAIL (4 small expected failures; badge... the badge does NOT go in the test — see Step 3)
- [ ] **Step 3: Edits**
  - `.gitignore`: append `dist/` (verify `build/` is already there).
  - Badge: measure real `Ran N` and put `tests-N passing` in `README.md:13`; add real PyPI badge: `[![PyPI](https://img.shields.io/pypi/v/hellochusquis.svg)](https://pypi.org/project/hellochusquis/)` after the Tests badge.
  - `sitemap.xml`: lastmod → today's ISO date.
  - `rm hellochusquis-landing.html`.
  - CHANGELOG: move full `## 5.4 — ...` block above `## 5.3`, without touching text.
- [ ] **Step 4: Run test → PASS; `tests.test_version_consistency` → PASS; suite OK**

### Task 2: Demo GIF for README/uneed

**Files:**
- Create: `docs/assets/demo.gif` (≤6MB)
- Modify: `README.md` (embed under the banner, 1 line)

**Interfaces:**
- Consumes: `videos/hellochusquis-ui-60s/renders/ui-60s.mp4`
- Produces: short loop 640-960px, 8-10s, first seconds

- [ ] **Step 1: Generate** (ffmpeg lives in /tmp)

Run: `PATH=/tmp:$PATH ffmpeg -y -t 10 -i videos/hellochusquis-ui-60s/renders/ui-60s.mp4 -vf "fps=12,scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse" docs/assets/demo.gif 2>&1 | tail -n 2`
- [ ] **Step 2: Verify weight**

Run: `ls -lh docs/assets/demo.gif; PATH=/tmp:$PATH ffprobe -v error -show_entries format=duration -of csv=p=0 docs/assets/demo.gif`
Expected: ≤6MB, ~10s. If >6MB: drop to `scale=720`, fps=10, re-run (once; if still over, `-t 8`).
- [ ] **Step 3: Embed README** (1 line under banner): `![Demo: 60s UI tour](docs/assets/demo.gif)` — real alt.
- [ ] **Step 4: No test** (binary; Step 2 evidence in report is enough).

### Task 3: Global green close

**Files:** none

- [ ] **Step 1: Run everything**

Run: `python3 -m unittest discover tests -q 2>&1 | tail -n 3` → OK
Run: `python3 -m ruff check . 2>&1 | tail -n 1` → clean
Run: `python3 cli.py doctor --contracts 2>&1 | tail -n 1` → 48/48
Run: `python3 -m unittest tests.test_catalog_freeze tests.test_version_consistency tests.test_packaging_hygiene -v 2>&1 | tail -n 4` → OK
Run: `python3 -m build 2>&1 | tail -n 1 && python3 -m twine check dist/* 2>&1 | tail -n 2 && rm -rf dist build hellochusquis.egg-info` → PASSED x2 (NO upload)

## Self-Review

1. **Spec coverage:** freeze ✓ (deferred absorbed), README ✓ (GIF+badges), SEO ✓ (sitemap), PyPI dry-run ✓ (T3), Deal/uneed ⏳ (needs owner, out of scope).
2. **Placeholder scan:** exact commands, lines, limits. Badge N is measured, never invented.
3. **Type consistency:** statics + 1 test only; no new signatures.
