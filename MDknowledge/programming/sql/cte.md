# SQL CTEs

- In SQL, `WITH x AS (SELECT ...)` names subqueries once for clarity and reuse.
- In SQL, multiple CTEs chain (`a AS (...), b AS (SELECT ... FROM a)`).
- In SQL, `WITH RECURSIVE` walks hierarchies (org charts, BOMs) iteratively.
- In SQL, CTEs optimize as fences or inlined depending on the engine version.
- In SQL, `MATERIALIZED`/`NOT MATERIALIZED` hints control Postgres inlining.
- In SQL, recursive CTEs need anchor plus recursive members unioned correctly.
- In SQL, cycle detection (`CYCLE` clause or visited arrays) guards graph walks.
- In SQL, prefer CTEs over nested subqueries past two levels for readability.
