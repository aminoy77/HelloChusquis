# Python context managers

- `with open(...)` guarantees closure on every exit path including exceptions.
- Custom managers implement `__enter__`/`__exit__` for paired setup/teardown.
- `contextlib.contextmanager` turns generator try/finally patterns into managers.
- `contextlib.suppress(ValueError)` skips expected exceptions declaratively.
- `contextlib.redirect_stdout` captures prints in tests without globals.
- `ExitStack` enters dynamic counts of managers programmatically.
- `__exit__` returning True suppresses the exception deliberately (rare).
- Lock acquisition/release belongs in managers, never manual pairs.
- Temporary directories/files via `tempfile` managers clean themselves.
- Nested `with` statements compose setup order left-to-right predictably.
