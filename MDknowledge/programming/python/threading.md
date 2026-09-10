# Python threading module

- In Python, the GIL allows one bytecode thread at a time, so threads suit IO-bound work, not CPU crunching.
- In Python, `threading.Thread(target=fn, args=(...), daemon=True)` runs callables concurrently.
- In Python, `thread.start()` launches and `thread.join(timeout)` waits for completion.
- In Python, `threading.Lock` guards shared state; hold it for the shortest span possible.
- In Python, `threading.RLock` permits re-entry by the owning thread for nested helpers.
- In Python, `queue.Queue` passes work between threads safely without manual locking.
- In Python, `threading.Event` signals readiness across threads with `set`, `wait`, and `clear`.
- In Python, `threading.local()` gives each thread its own isolated namespace.
- In Python, daemon threads die with the process; join workers for clean shutdowns.
- In Python, `concurrent.futures.ThreadPoolExecutor` manages pools with `submit` and `map`.
