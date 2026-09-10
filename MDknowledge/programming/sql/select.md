# SQL SELECT

- In SQL, `SELECT col1, col2 FROM t;` reads specific columns; avoid `SELECT *` in production code.
- In SQL, `WHERE` filters rows before grouping: `SELECT * FROM t WHERE age > 18;`.
- In SQL, `ORDER BY col DESC` sorts results; add `LIMIT 10` to cap the row count.
- In SQL, `LIKE 'A%'` matches prefixes, `%` matches anything, and `_` matches exactly one character.
- In SQL, `IN (1, 2, 3)` and `BETWEEN 10 AND 20` (inclusive) express set and range membership.
- In SQL, NULL is never equal to anything, not even itself: use `IS NULL` / `IS NOT NULL`, never `= NULL`.
- In SQL, `COUNT(*)` counts rows including NULLs while `COUNT(col)` skips NULL values in that column.
- In SQL, `GROUP BY dept` plus aggregates (`SUM`, `AVG`, `MIN`, `MAX`) summarizes per group.
- In SQL, `HAVING` filters groups after aggregation; `WHERE` cannot reference aggregate results.
- In SQL, `DISTINCT` drops duplicate rows from the result set.
- In SQL, column aliases use `AS` (`SELECT salary AS pay`) and can be referenced in `ORDER BY`.
- In SQL, `CASE WHEN cond THEN a ELSE b END` branches inline within a query.
- In SQL, `COALESCE(a, b)` returns the first non-NULL argument, ideal for defaults.
- In SQL, subqueries in `WHERE x IN (SELECT ...)` filter by another query's results.
- In SQL, `EXISTS (SELECT 1 ...)` tests for matching rows and usually beats `IN` on large sets.
- In SQL, `LIMIT`/`OFFSET` paginate, but keyset pagination (`WHERE id > last`) scales better than deep offsets.
- In SQL, `UNION` merges result sets dropping duplicates; `UNION ALL` keeps them and runs faster.
- In SQL, comments use `--` for lines and `/* ... */` for blocks.
