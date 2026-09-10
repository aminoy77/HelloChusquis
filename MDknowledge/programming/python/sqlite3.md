# Python sqlite3 module

- In Python, `sqlite3.connect(path)` opens databases and `:memory:` keeps them transient for tests.
- In Python, always parameterize with `?` placeholders; string formatting invites SQL injection.
- In Python, `with conn:` blocks commit on success and roll back on exceptions automatically.
- In Python, `conn.row_factory = sqlite3.Row` enables name-based column access on results.
- In Python, `CREATE TABLE IF NOT EXISTS` makes schema setup idempotent across runs.
- In Python, `cursor.lastrowid` reports the AUTOINCREMENT id of the inserted row.
- In Python, `executemany` batches inserts far faster than looping `execute`.
- In Python, `PRAGMA journal_mode=WAL` improves concurrent read behavior for local apps.
- In Python, `conn.execute('PRAGMA foreign_keys=ON')` enforces declared foreign-key constraints.
- In Python, set `check_same_thread=False` only with external locking for multithreaded use.
