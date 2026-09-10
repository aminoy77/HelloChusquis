# Python debugging tools

- `breakpoint()` drops into pdb with step/next/continue/print commands.
- `python -m pdb script.py` debugs from the first line deterministically.
- `faulthandler.dump_traceback_later` exposes hangs in production safely.
- `cProfile` plus `pstats` rank function costs for optimization targets.
- `timeit` micro-benchmarks snippets with proper repetition statistics.
- `tracemalloc` attributes memory growth to allocating code lines.
- `logging` with levels beats print archaeology in long-lived services.
- `-X dev` mode surfaces warnings (unclosed resources, bad encodings) early.
- Post-mortem (`pdb.post_mortem`) inspects crashed states from tracebacks.
- Reproduce minimally first; debuggers amplify understanding, not substitutes.
