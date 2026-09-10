# Go slices and maps

- In Go, slices share backing arrays: `b := a[1:3]` aliases, so appends may clobber siblings.
- In Go, `append` returns the updated slice; always assign the result back.
- In Go, `copy(dst, src)` duplicates elements and returns the count moved.
- In Go, full slice expressions `a[1:3:3]` cap capacity to prevent accidental overwrites.
- In Go, nil slices read fine (`len` 0, range skips) but appending allocates fresh.
- In Go, maps are reference types: assignment shares, and iteration order randomizes.
- In Go, `delete(m, k)` removes keys safely, even absent ones.
- In Go, structs as map keys must be comparable (no slices inside).
- In Go, `make(map[string]int, hint)` pre-sizes maps when the count is known.
- In Go, sort map output explicitly since ranging never guarantees order.
