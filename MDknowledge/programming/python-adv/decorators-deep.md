# Python decorators deep (example)

- Decorators receive functions returning replacements at import time.
- `functools.wraps` preserves names, docs, and signatures through wrapping.
- Parameterized decorators need an outer factory returning the real decorator.
- Class decorators transform whole classes (registries, dataclasses).
- `@lru_cache` memoizes pure functions by hashable arguments.
- Order stacks bottom-up: lowest decorator applies first.
- Descriptor protocol powers `@property` under the hood.
- Preserve signatures with `functools.wraps` plus `__wrapped__` chains.
- Testing decorated code targets unwrapped `__wrapped__` functions directly.
- Over-decorating obscures tracebacks; keep stacks shallow and named.
