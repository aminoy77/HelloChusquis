# Python copy module

- In Python, assignment never copies: `b = a` aliases the same object.
- In Python, `copy.copy(x)` makes a shallow copy sharing nested objects.
- In Python, `copy.deepcopy(x)` clones the full object graph recursively.
- In Python, `list(a)`, `dict(a)`, and `a[:]` are idiomatic shallow copies for builtins.
- In Python, `deepcopy` memoizes and preserves shared references and cycles correctly.
- In Python, custom classes tune copying via `__copy__` and `__deepcopy__` hooks.
- In Python, immutable objects (tuples of immutables, strings) need no copying at all.
- In Python, `copy` then mutate is safer than mutating shared defaults in function signatures.
- In Python, NumPy arrays and pandas frames have their own `.copy()` with deep semantics.
- In Python, profile before deep-copying large graphs; copies cost memory and time.
