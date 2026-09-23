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

## End-to-end accuracy, local 1B (measured 2026-09-23)

Same 35 questions answered by **llama3.2:1b via local Ollama**, bare versus
knowledge-layered (production `recall_context` prepended, no tools), graded by
gold-substring match. Rerun: `OLLAMA_E2E_MODEL=llama3.2:1b python3
tests/test_probe_e2e_1b.py --write-docs` (writes `probe-e2e-1b.csv`/`.json`).

Result: **bare 7/35 (20%) → layered 26/35 (74%)**. The KB more than triples
the tiny model's factual accuracy; grading is strict substring, so paraphrased
correct answers can count as misses on both sides. This run replaced the old
"~1B 55→90% (projected)" estimate in `assets/kb-accuracy.svg`.

Launch guidance: 1B models follow instructions unreliably (same prompt
answered "ok" once and "No." another time; occasional hallucinated tool
calls). Default new users to 3B or larger; treat 1B as experimental
minimum for tinkerers, never as the first-run experience.

## The other number on the landing page

The "86% → 100% accuracy" chart (`assets/kb-accuracy.svg`) is a separate,
manual end-to-end run: a local 3B model (qwen2.5-coder:3b) answering the same
style of factual questions bare versus knowledge-layered. That run observed
97% retrieval coverage; the automated probe above, after a recall-ranking fix
(SQL orders candidates by token-hit count, Python re-ranks with pool IDF),
scores 100%. The CI gate (`tests/test_probe_35q.py`) pins coverage ≥ 90% so
neither number can silently rot.
