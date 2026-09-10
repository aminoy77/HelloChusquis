# Python functools module

- In Python, `@functools.lru_cache(maxsize=...)` memoizes pure function calls by arguments.
- In Python, `@functools.cache` is the unbounded variant for strictly finite key spaces.
- In Python, `@functools.wraps` inside decorators preserves name, docstring, and signature.
- In Python, `functools.partial(f, x)` freezes leading arguments into a new callable.
- In Python, `functools.reduce(fn, items, init)` folds iterables left to right with a start value.
- In Python, `@functools.total_ordering` derives all comparisons from `__eq__` plus one ordering method.
- In Python, `functools.singledispatch` routes generic functions on the first argument's type.
- In Python, `functools.cmp_to_key` adapts old comparator functions to `key=` parameters.
- In Python, `lru_cache` requires hashable arguments; convert lists to tuples first.
- In Python, `cache_clear()` and `cache_info()` reset and inspect memoization during tests.
