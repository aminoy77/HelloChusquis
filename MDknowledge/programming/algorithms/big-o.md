# Big-O notation

- Big-O bounds worst-case growth ignoring constants: O(1), O(log n), O(n), O(n log n), O(n²), O(2ⁿ).
- O(1) hash lookups beat O(log n) trees for point queries at memory cost.
- Binary search O(log n) halves billion-scale spaces in ~30 steps.
- Doubling input size doubles O(n) cost but quadruples O(n²) cost.
- Amortized analysis spreads occasional expensive ops (vector growth) across many cheap ones.
- Space complexity trades against time: memoization buys speed with memory.
- Best/average/worst cases differ: quicksort averages n log n, worsts at n².
- NP-complete problems (TSP, SAT) lack known polynomial solutions; approximate instead.
- Profile before optimizing: constants and I/O dominate below ~10⁵ elements.
- State n explicitly: O(n·m) on grids differs from O(n) on lists.
