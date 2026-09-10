# Sorting algorithms

- Quicksort averages O(n log n) but degrades to O(n²) on bad pivots without randomization.
- Mergesort guarantees O(n log n) using O(n) extra space for merging.
- Heapsort guarantees O(n log n) in place but with poor cache behavior.
- Insertion sort wins on tiny or nearly-sorted inputs inside hybrid sorts (Timsort).
- Counting/radix sorts hit O(n) for bounded integer keys.
- Stability preserves equal-element order; mergesort is stable, heapsort is not.
- Comparison sorts cannot beat O(n log n) worst-case (decision-tree bound).
- Python sorted(), C++ std::sort, and Java Arrays.sort are tuned hybrids — prefer them.
- External sorting chunks runs to disk then k-way merges beyond-RAM data.
- Benchmark with realistic data: constant factors beat big-O on small n.
- Bubble sort compares adjacent pairs repeatedly in O(n²) time, mainly a teaching example.
