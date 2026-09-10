# SQL ALTER TABLE

- `ALTER TABLE t ADD COLUMN c TYPE` extends live tables (with defaults for NOT NULL).
- Adding nullable columns is instant; backfills decide the real cost.
- `ALTER COLUMN TYPE` rewrites tables on some engines — test on copies first.
- Rename-then-add patterns achieve zero-downtime column swaps safely.
- `DROP COLUMN` reclaims space lazily; some engines only hide it.
- Concurrent index builds (`CONCURRENTLY`) avoid write locks in production.
- Check constraints validate existing rows unless marked `NOT VALID` first.
- Renaming tables breaks views/functions referencing old names — audit first.
- Online schema-change tools (pt-osc, ghost) shadow-copy huge tables.
- Every ALTER deserves a rollback migration reviewed alongside.
