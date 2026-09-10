# SQL JOINs

- In SQL, `INNER JOIN` keeps only rows with matches on both sides of the `ON` condition.
- In SQL, `LEFT JOIN` keeps every left row, filling NULLs where no right row matches.
- In SQL, `RIGHT JOIN` mirrors LEFT JOIN, keeping every right row instead.
- In SQL, `FULL OUTER JOIN` keeps unmatched rows from both sides with NULLs on the missing side.
- In SQL, join conditions belong in `ON`, row filters in `WHERE`; mixing them changes outer-join results.
- In SQL, filtering the nullable side of a LEFT JOIN in `WHERE` silently converts it into an INNER JOIN.
- In SQL, table aliases (`FROM users u`) shorten queries and are required for self-joins.
- In SQL, a self-join queries one table twice under two aliases, e.g. employees to their managers.
- In SQL, `JOIN ... USING (col)` merges same-named key columns when both sides share the name.
- In SQL, foreign keys (`REFERENCES`) declare relationships; joins still need explicit `ON` clauses.
- In SQL, `CROSS JOIN` produces every combination (cartesian product) and explodes row counts fast.
- In SQL, multiple joins chain left to right; parenthesize or order them when mixing inner and outer joins.
- In SQL, `SELECT` columns from joined tables should be qualified (`u.name`) to avoid ambiguity errors.
- In SQL, joining on indexed columns keeps nested-loop joins fast; unindexed joins degrade on large tables.
- In SQL, `EXPLAIN` (or `EXPLAIN ANALYZE`) shows the join plan before tuning indexes.
- In SQL, aggregating after a one-to-many join multiplies rows; pre-aggregate the many side in a subquery first.
