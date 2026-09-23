"""35-question factual probe: KB retrieval coverage through the production path.

Measures whether ``recall_context`` (the exact function the agent calls per
turn, default limit/top-k) surfaces the ingested MDknowledge fact for each
natural question. Runs fully offline against an isolated temp DB.

Regenerate the committed receipts (docs/probe-35q.csv) with:
    python3 tests/test_probe_35q.py --write-docs
"""
import csv
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import core.db_memory as db_memory

# (question, acceptable gold substrings, all lowercase-matched)
QUESTIONS = [
    ("Which city was a great Silk Road city in Uzbekistan?", ["samarkand"]),
    ("What language do people in Cuba speak?", ["spanish"]),
    ("About how many people live in Rwanda?", ["14 million"]),
    ("Bulgaria is in which part of Europe?", ["eastern europe"]),
    ("Which lake's ten peaks appear on old bills?", ["moraine"]),
    ("What is the chemical symbol and atomic number of Ytterbium?", ["yb", "70"]),
    ("What state is iron at room temperature?", ["solid"]),
    ("What do red blood cells haul?", ["oxygen"]),
    ("What happens where continents collide?", ["crumple", "himalayas"]),
    ("Who generalized inoculation after Jenner?", ["pasteur"]),
    ("What formula solves second-degree polynomial equations?", ["quadratic"]),
    ("How many people trigger the birthday paradox at fifty percent?", ["23"]),
    ("What does the gambler's fallacy mistake for balancing forces?", ["streaks"]),
    ("What does the law of cosines generalize?", ["pythagoras"]),
    ("What does the second derivative test classify?", ["critical points"]),
    ("In which year did Watt's steam engine power factories?", ["1776"]),
    ("What arrangement created the 38th parallel division?", ["1945", "soviet"]),
    ("What sentence did Mandela get at the Rivonia Trial?", ["life imprisonment"]),
    ("What devastated Aztec defenders faster than Spanish weapons?", ["smallpox"]),
    ("Which city did sanctions squeeze economically over apartheid?", ["pretoria"]),
    ("In C, what does break exit?", ["innermost loop"]),
    ("Which match variants do CSS attribute selectors support?", ["substring", "prefix"]),
    ("What does JavaScript indexOf return when missing?", ["-1"]),
    ("What does Python get_text with strip do?", ["cleans content"]),
    ("What do macro commands compose?", ["primitives"]),
    ("What does on the ball mean?", ["alert"]),
    ("Does fewer fit countable or uncountable items?", ["countable"]),
    ("What does the rule of three structure messages into?", ["triads"]),
    ("What does formal writing avoid?", ["contractions"]),
    ("Which verb goes with homework, make or do?", ["do homework"]),
    ("How many kilometers in one mile?", ["1.609"]),
    ("How many megajoules in one kWh?", ["3.6"]),
    ("Since when does Unix time count seconds?", ["1970"]),
    ("How many Fahrenheit is zero Celsius?", ["32", "fahrenheit"]),
    ("How many km/h is one knot?", ["1.852"]),
]

COVERAGE_FLOOR = 0.90


def run_probe():
    """Ingest the real repo KB into a temp DB and score all questions."""
    tmpdir = tempfile.mkdtemp()
    prev = db_memory.MEMORY_DB_PATH
    db_memory.MEMORY_DB_PATH = Path(tmpdir) / "probe.db"
    try:
        ingested = db_memory.load_knowledge()
        rows = []
        for question, golds in QUESTIONS:
            ctx = db_memory.recall_context(question).lower()
            hit = any(g.lower() in ctx for g in golds)
            snippet = next((g for g in golds if g.lower() in ctx), "")
            rows.append({"question": question, "hit": hit, "matched": snippet})
        covered = sum(1 for r in rows if r["hit"])
        return {"ingested": ingested, "covered": covered, "total": len(rows), "rows": rows}
    finally:
        db_memory.MEMORY_DB_PATH = prev


def write_docs_csv(path, result):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["question", "hit", "matched"])
        writer.writeheader()
        for row in result["rows"]:
            writer.writerow({"question": row["question"], "hit": int(row["hit"]),
                             "matched": row["matched"]})


class TestProbe35Q(unittest.TestCase):
    def test_retrieval_coverage_floor(self):
        result = run_probe()
        coverage = result["covered"] / result["total"]
        self.assertGreater(result["ingested"], 1000, "KB ingest looks broken")
        self.assertGreaterEqual(
            coverage, COVERAGE_FLOOR,
            f"KB retrieval coverage {result['covered']}/{result['total']} below floor",
        )


if __name__ == "__main__":
    if "--write-docs" in sys.argv:
        res = run_probe()
        out = Path(__file__).resolve().parent.parent / "docs" / "probe-35q.csv"
        write_docs_csv(str(out), res)
        print(f"{res['covered']}/{res['total']} coverage, ingested {res['ingested']} -> {out}")
    else:
        unittest.main()
