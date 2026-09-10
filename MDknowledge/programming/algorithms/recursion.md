# Recursion

- Recursion needs a base case plus progress toward it, or it overflows the stack.
- Stack depth ~1000 (Python) bounds naive recursion; iterate deep loops instead.
- Tail calls still consume frames in Python/Java; only some languages optimize them.
- Divide-and-conquer (mergesort, quicksort) splits, conquers, and combines recursively.
- Backtracking explores choices depth-first, undoing moves that dead-end (N-queens, Sudoku).
- Memoization converts exponential recursion to polynomial by caching subresults.
- Recursion mirrors inherently recursive data: trees, ASTs, filesystems, JSON.
- Mutual recursion alternates functions; keep contracts explicit to avoid loops.
- Trampolines flatten recursion into iteration for stack safety in functional code.
- Prove correctness by induction matching the recursive structure.
