# SQL GROUP BY

- In SQL, `GROUP BY dept` collapses rows so aggregates summarize each group.
- In SQL, every non-aggregated SELECT column must appear in the GROUP BY list.
- In SQL, `COUNT(*)`, `SUM`, `AVG`, `MIN`, `MAX` aggregate within each group.
- In SQL, `HAVING COUNT(*) > 5` filters groups; WHERE cannot see aggregates.
- In SQL, `COUNT(DISTINCT user_id)` counts unique values per group.
- In SQL, `GROUP_CONCAT`/`string_agg` join group members into delimited strings.
- In SQL, `GROUP BY` on expressions needs the same expression, not its alias, in strict databases.
- In SQL, `WITH ROLLUP`/`GROUPING SETS` add subtotal rows to grouped reports.
- In SQL, filter rows in WHERE before grouping to shrink aggregation input.
- In SQL, `SELECT DISTINCT` dedupes whole rows without any grouping.
