# Python generators deep (example)

- Generators pause at `yield`, resuming with sent values via `.send()`.
- `yield from` delegates to sub-generators transparently.
- Generator expressions `(x*x for x in it)` stream without list material.
- `itertools` composes lazy pipelines (chain, islice, groupby) elegantly.
- Infinite generators (counters, streams) pair with `islice` consumers.
- `close()` injects GeneratorExit for resource cleanup deterministically.
- Coroutines (pre-asyncio) drove on `.send()`-based schedulers historically.
- `contextlib.contextmanager` builds managers from generator functions.
- Memory stays flat streaming gigabytes through generator pipelines.
- Debug with `list(islice(gen, 5))` snapshots without exhaustion.
