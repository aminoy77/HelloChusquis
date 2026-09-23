# 35-question factual probe — receipts

Date: 2026-09-23. Rerun anytime: `python3 -m pytest tests/test_probe_35q.py -q`
Regenerate per-question results: `python3 tests/test_probe_35q.py --write-docs` (writes `probe-35q.csv`).

## What this measures

Retrieval coverage through the **production recall path**: each question goes to
`core.db_memory.recall_context()` with production defaults (top-3, 800 chars) —
the exact function the agent calls before every turn. A question scores a hit
when the ingested MDknowledge fact appears in the returned context. Fully
offline against an isolated temp DB; no provider credentials needed.

Result: **35/35 (100%)**. Raw per-question rows: `probe-35q.csv`.

## The other number on the landing page

The "86% → 100% accuracy" chart (`assets/kb-accuracy.svg`) is a separate,
manual end-to-end run: a local 3B model (qwen2.5-coder:3b) answering the same
style of factual questions bare versus knowledge-layered. That run observed
97% retrieval coverage; the automated probe above, after a recall-ranking fix
(SQL orders candidates by token-hit count, Python re-ranks with pool IDF),
scores 100%. The CI gate (`tests/test_probe_35q.py`) pins coverage ≥ 90% so
neither number can silently rot.
