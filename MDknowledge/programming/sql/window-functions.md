# SQL window functions

- In SQL, `ROW_NUMBER() OVER (ORDER BY x)` ranks rows without collapsing them like GROUP BY.
- In SQL, `PARTITION BY dept` restarts window calculations per group independently.
- In SQL, `RANK()` gaps ties while `DENSE_RANK()` keeps numbering consecutive.
- In SQL, `LAG(col)`/`LEAD(col)` peek at neighboring rows for deltas and streaks.
- In SQL, `SUM(x) OVER (PARTITION BY d ORDER BY t)` builds running totals per group.
- In SQL, `FIRST_VALUE`/`LAST_VALUE` fetch frame edges; mind the default frame endpoints.
- In SQL, explicit frames (`ROWS BETWEEN 6 PRECEDING AND CURRENT ROW`) define moving averages.
- In SQL, `NTILE(4)` buckets rows into quartiles for cohort analysis.
- In SQL, window functions evaluate after WHERE/GROUP BY, so filter first for speed.
- In SQL, `FILTER (WHERE ...)` aggregates conditionally inside windowed selects.
