# SQL UPDATE and DELETE

- `UPDATE t SET c = v WHERE ...` without WHERE rewrites every row — always qualify.
- Preview impact with the same WHERE in a SELECT before mutating.
- Transactions wrap multi-statement mutations for atomic rollback safety.
- `RETURNING *` (Postgres) inspects affected rows without re-querying.
- Batch huge updates in chunks with pauses to avoid lock pileups.
- `DELETE` logs per row; `TRUNCATE` resets fast without row triggers.
- Cascades (`ON DELETE CASCADE`) automate child cleanup at design time.
- Soft deletes (`deleted_at`) preserve history where audits demand it.
- Verify row counts after each mutation against expectations immediately.
- Backups precede manual production writes, no matter how trivial they seem.
