# SQL WHERE

- In SQL, `WHERE age >= 18 AND country = 'CL'` combines predicates with AND/OR/NOT.
- In SQL, `AND` binds tighter than `OR`; parenthesize mixed conditions explicitly.
- In SQL, `IN (...)` replaces long `OR` chains over the same column.
- In SQL, `BETWEEN 10 AND 20` is inclusive on both ends, unlike half-open ranges.
- In SQL, `LIKE 'A%'` prefix-matches; leading `%` patterns defeat plain indexes.
- In SQL, `IS NULL`/`IS NOT NULL` test nullness since `= NULL` is never true.
- In SQL, `NOT IN` with a NULL in the list matches nothing; prefer `NOT EXISTS`.
- In SQL, date ranges as `d >= '2024-01-01' AND d < '2024-02-01'` beat month functions for indexes.
- In SQL, `EXISTS` short-circuits on the first matching row efficiently.
- In SQL, `WHERE 1=1` starters simplify dynamically appended `AND` filters.
