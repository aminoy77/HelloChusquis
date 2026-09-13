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
            # Siembra con la API publica de escritura de turnos (misma familia
            # que save_session/save_summary de tests/test_db_memory.py:
            # persiste sesion + entrada buscable) y busca palabra distintiva.
            db_memory.save_turn(fact, fact)
            probe = max(words, key=len)
            ctx = db_memory.recall_context(probe)
            if probe in ctx.lower():
                hits += 1
        self.assertGreater(total, 0)
        self.assertGreaterEqual(hits / total, 0.95, f"cobertura recall {hits}/{total}")
