# Python dataclasses module

- In Python, `@dataclass` generates `__init__`, `__eq__`, and `__repr__` from annotations.
- In Python, `field(default_factory=list)` gives each instance its own mutable default.
- In Python, `frozen=True` makes instances immutable and hashable when all fields qualify.
- In Python, `field(compare=False)` excludes noisy fields from generated equality.
- In Python, `__post_init__` validates or derives attributes right after construction.
- In Python, `dataclasses.replace(obj, x=1)` copies with changes, like immutable updates.
- In Python, `asdict()` and `astuple()` convert instances recursively for serialization.
- In Python, `order=True` adds sorting from the field declaration order.
- In Python, `kw_only=True` (3.10+) forces keyword construction for clarity.
- In Python, prefer dataclasses over dicts when shapes are fixed and documented.
