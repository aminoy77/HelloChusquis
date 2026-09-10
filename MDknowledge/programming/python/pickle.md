# Python pickle module

- In Python, `pickle.dumps(obj)` serializes and `pickle.loads(data)` restores Python objects.
- In Python, never unpickle untrusted data: it can execute arbitrary code on load.
- In Python, `pickle.HIGHEST_PROTOCOL` picks the newest, most efficient format.
- In Python, `__getstate__`/`__setstate__` customize what pickle saves and restores.
- In Python, `__reduce__` controls reconstruction for exotic classes.
- In Python, lambdas, open files, sockets, and threads cannot be pickled.
- In Python, `copyreg` registers pickling support for third-party types.
- In Python, prefer JSON for cross-language data and reserve pickle for trusted Python-to-Python state.
- In Python, `shelve` persists dict-like objects to disk using pickle underneath.
- In Python, `pickletools.dis` disassembles pickles when debugging corrupt payloads.
