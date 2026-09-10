# SQL transactions

- In SQL, `BEGIN; ... COMMIT;` groups statements atomically; `ROLLBACK` undoes the group.
- In SQL, ACID promises atomicity, consistency, isolation, and durability per transaction.
- In SQL, keep transactions short: long ones hold locks and bloat write-ahead logs.
- In SQL, `READ COMMITTED` is the common isolation default; `SERIALIZABLE` trades speed for safety.
- In SQL, deadlocks abort one party with a retryable error; retry with backoff, not blindly.
- In SQL, `SAVEPOINT sp` plus `ROLLBACK TO sp` undoes part of a transaction surgically.
- In SQL, DDL auto-commits in some databases, splitting surrounding transactions unexpectedly.
- In SQL, `SELECT ... FOR UPDATE` locks chosen rows against concurrent writers.
- In SQL, optimistic locking via version columns avoids locks for low-contention updates.
- In SQL, autocommit wraps every lone statement; batch related writes explicitly.
