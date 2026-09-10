# Python weak references

- In Python, `weakref.ref(obj)` references without preventing collection.
- In Python, `WeakValueDictionary` caches that evaporate under memory pressure.
- In Python, `WeakSet` tracks listeners without pinning them alive.
- In Python, callbacks on collection (`weakref.ref(o, cb)`) drive cleanup hooks.
- In Python, most builtins (int, str, tuple) reject weakrefs; classes allow them.
- In Python, `__slots__` classes need `__weakref__` listed for weak support.
- In Python, cyclic garbage needs no help, but weakrefs break cycles early.
- In Python, GUI frameworks use weakrefs for signal-slot connections safely.
