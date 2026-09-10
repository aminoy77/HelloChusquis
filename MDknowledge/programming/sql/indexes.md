# SQL indexes

- In SQL, `CREATE INDEX idx ON t(col)` speeds selective WHERE, JOIN, and ORDER BY on col.
- In SQL, indexes accelerate reads but slow writes and consume disk; index deliberately.
- In SQL, composite indexes serve leftmost-prefix queries: `(a, b)` covers `a` and `a+b`, not `b` alone.
- In SQL, `UNIQUE` indexes enforce deduplication at write time.
- In SQL, `EXPLAIN` reveals scans versus seeks before adding indexes blindly.
- In SQL, leading-wildcard `LIKE '%x'` cannot use plain B-tree indexes.
- In SQL, covering indexes include all selected columns, answering queries without table visits.
- In SQL, over-indexed tables stall inserts; drop indexes unused by real query plans.
- In SQL, primary keys create clustered/unique backing indexes automatically.
- In SQL, `ANALYZE`/`VACUUM ANALYZE` refreshes planner statistics after bulk loads.
