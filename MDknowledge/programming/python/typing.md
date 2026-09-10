# Python typing module

- In Python, `def f(x: int) -> str:` annotates parameters and returns for checkers, not runtime.
- In Python, `Optional[str]` means `str | None`; handle the None case before use.
- In Python, `list[int]` and `dict[str, int]` generics work natively since Python 3.9.
- In Python, `mypy` and `pyright` verify annotations statically in CI.
- In Python, `Any` disables checking locally; prefer precise types or `object` narrowing.
- In Python, `TypeVar('T')` writes generic helpers preserving input-output type relations.
- In Python, `Protocol` defines structural interfaces satisfied implicitly by matching classes.
- In Python, `TypedDict` types fixed-shape dicts like JSON payloads field by field.
- In Python, `Literal['a', 'b']` restricts values to an exact allowed set.
- In Python, `cast(T, x)` asserts a type to the checker without runtime effect.
