# Decorator pattern

- Decorator wraps objects adding behavior without subclassing.
- Python `@decorators`, Java I/O streams, and middleware chains all decorate.
- Order matters: caching outside auth differs from auth outside caching.
- Transparent decorators preserve the wrapped interface exactly.
- Excess layers obscure stack traces; keep chains shallow and named.
- Composition of small decorators beats monolithic subclasses.
- Immutable inputs make decorator pipelines safe to reorder and cache.
- Log decorator arguments at boundaries for debuggable pipelines.
- Prefer language decorator syntax over manual wrapper construction.
- Test each decorator alone, then one representative full stack.
