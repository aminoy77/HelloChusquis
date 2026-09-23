"""End-to-end accuracy probe: bare model vs knowledge-layered, local 1B model.

Runs the 35 factual questions from tests/test_probe_35q.py against a local
Ollama model twice: bare (no context) and layered (production
``recall_context`` prepended, same as the agent does per turn). Grades by
gold-substring match. Fully local; needs Ollama + model pulled.

Run:
    OLLAMA_E2E_MODEL=llama3.2:1b python3 tests/test_probe_e2e_1b.py --write-docs
Skipped in CI unless OLLAMA_E2E=1 is set and the model answers.
"""
import csv
import os
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import yaml

import core.db_memory as db_memory
from core.provider import ProviderPool
from tests.test_probe_35q import QUESTIONS

MODEL = os.environ.get("OLLAMA_E2E_MODEL", "llama3.2:1b")
PROVIDER = os.environ.get("OLLAMA_E2E_PROVIDER", "Ollama (local)-3")
CONFIG_PATH = Path.home() / ".hellochusquis" / "config.yaml"

BARE_SYSTEM = "Answer concisely in one short sentence."
LAYERED_SYSTEM = ("Answer concisely in one short sentence. "
                  "Use the reference context below when relevant.\n{ctx}")


def _pool():
    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    return ProviderPool(config=cfg)


def _ask(pool, system, question, timeout_s=180):
    resp = pool.chat_with_retry(
        [{"role": "system", "content": system}, {"role": "user", "content": question}],
        provider_name=PROVIDER, model=MODEL,
    )
    try:
        return str(resp["choices"][0]["message"].get("content") or "")
    except (KeyError, IndexError, TypeError):
        return ""


def run_e2e(progress=False):
    pool = _pool()
    # Availability probe (skips CI without Ollama/model).
    probe = _ask(pool, BARE_SYSTEM, "Reply with the single word: ready.")
    if not probe.strip():
        raise unittest.SkipTest(f"model {MODEL} via {PROVIDER} unavailable")
    rows = []
    for i, (question, golds) in enumerate(QUESTIONS):
        t0 = time.time()
        bare = _ask(pool, BARE_SYSTEM, question)
        bare_hit = any(g.lower() in bare.lower() for g in golds)
        ctx = db_memory.recall_context(question)
        layered = _ask(pool, LAYERED_SYSTEM.format(ctx=ctx), question)
        layered_hit = any(g.lower() in layered.lower() for g in golds)
        rows.append({"question": question, "bare_hit": bare_hit,
                     "layered_hit": layered_hit, "secs": round(time.time() - t0, 1)})
        if progress:
            print(f"[{i + 1}/{len(QUESTIONS)}] bare={int(bare_hit)} kb={int(layered_hit)}", flush=True)
    return rows


def summarize(rows):
    n = len(rows)
    bare = sum(1 for r in rows if r["bare_hit"])
    layered = sum(1 for r in rows if r["layered_hit"])
    return {"total": n, "bare": bare, "layered": layered,
            "bare_pct": round(100 * bare / n, 1), "layered_pct": round(100 * layered / n, 1)}


class TestProbeE2E1B(unittest.TestCase):
    def test_e2e_1b(self):
        if os.environ.get("OLLAMA_E2E") != "1":
            raise unittest.SkipTest("set OLLAMA_E2E=1 with local Ollama running")
        rows = run_e2e()
        s = summarize(rows)
        print(f"\n1B E2E: bare {s['bare']}/{s['total']} ({s['bare_pct']}%) "
              f"-> layered {s['layered']}/{s['total']} ({s['layered_pct']}%)")
        self.assertGreaterEqual(s["layered"], s["bare"], "KB layering must not hurt")


if __name__ == "__main__":
    if "--write-docs" in sys.argv:
        rows = run_e2e(progress=True)
        s = summarize(rows)
        docs = Path(__file__).resolve().parent.parent / "docs"
        with open(docs / "probe-e2e-1b.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["question", "bare_hit", "layered_hit", "secs"])
            w.writeheader()
            for r in rows:
                w.writerow({"question": r["question"], "bare_hit": int(r["bare_hit"]),
                            "layered_hit": int(r["layered_hit"]), "secs": r["secs"]})
        (docs / "probe-e2e-1b.json").write_text(
            __import__("json").dumps({"model": MODEL, "provider": PROVIDER, **s}, indent=2),
            encoding="utf-8")
        print(f"E2E {MODEL}: bare {s['bare']}/{s['total']} layered {s['layered']}/{s['total']}")
    else:
        unittest.main()
