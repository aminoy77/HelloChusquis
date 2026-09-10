# SQL subqueries

- In SQL, `WHERE id IN (SELECT ...)` filters by another query's result set.
- In SQL, scalar subqueries in SELECT must return exactly one row and column.
- In SQL, derived tables (`FROM (SELECT ...) t`) need aliases in most databases.
- In SQL, `EXISTS` beats `IN` when the subquery is large or nullable.
- In SQL, correlated subqueries reference outer rows and run once per outer row.
- In SQL, `WITH cte AS (...)` names subqueries once for readability and reuse.
- In SQL, recursive CTEs (`WITH RECURSIVE`) walk hierarchies like org charts.
- In SQL, `LATERAL`/cross-apply subqueries see preceding FROM items per row.
- In SQL, `ANY`/`ALL` compare against subquery sets without full materialization.
- In SQL, flatten hot-path correlated subqueries into joins for the optimizer.
