# Dynamic programming

- Dynamic programming solves overlapping subproblems once each, top-down (memo) or bottom-up (table).
- Fibonacci recursion is exponential naive, linear memoized — the canonical lesson.
- Knapsack 0/1 fills a capacity table in O(n·W) pseudo-polynomial time.
- Longest common subsequence aligns DNA and diffs via grid recurrence.
- Edit distance counts insertions/deletions/substitutions between strings.
- Coin change counts combinations with unbounded coins via ordered loops.
- State compression (rolling arrays) cuts DP memory from O(n²) to O(n).
- Optimal substructure plus overlapping subproblems signal DP applicability.
- Greedy fails where local optima mislead; DP enumerates choices safely.
- Reconstruct solutions by backpointers, not just optimal values.
