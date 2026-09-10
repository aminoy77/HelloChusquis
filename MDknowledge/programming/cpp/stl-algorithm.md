# C++ algorithms

- In C++, `<algorithm>` hosts `sort`, `find`, `count`, `copy`, and `transform` for ranges.
- In C++, `std::sort(v.begin(), v.end())` averages O(n log n) with custom comparators.
- In C++, `std::find` returns `end()` on miss; always compare before dereferencing.
- In C++, `std::transform` maps ranges into outputs without hand loops.
- In C++, `std::accumulate(v.begin(), v.end(), 0)` folds sums with explicit init type.
- In C++, `std::remove` compacts survivors forward; pair with `erase` to actually shrink (erase-remove).
- In C++, `std::all_of/any_of/none_of` replace flag-variable predicate loops.
- In C++, `std::clamp(v, lo, hi)` bounds values without branch chains.
- In C++, `std::iota(v.begin(), v.end(), 0)` fills ascending sequences directly.
- In C++, C++20 ranges (`v | std::views::filter(...)`) compose lazily like pipelines.
