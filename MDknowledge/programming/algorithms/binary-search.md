# Binary search

- Binary search finds targets in sorted arrays in O(log n) time.
- Maintain lo/hi bounds; mid = (lo+hi)//2 avoids overflow in fixed-width languages.
- Move lo = mid+1 when array[mid] is too small, else hi = mid for lower bounds.
- std::binary_search, Python bisect, and Java Arrays.binarySearch implement it correctly.
- Off-by-one errors dominate: test empty, single-element, and missing-target cases.
- Bisect_left returns insertion points keeping sorted order for new elements.
- Binary search generalizes to monotonic predicates (first bad version problems).
- Rotated sorted arrays need one extra comparison to pick the ordered half.
- Galloping/exponential search bounds unknown-length ranges before bisecting.
- Proving termination: the interval strictly shrinks every iteration.
