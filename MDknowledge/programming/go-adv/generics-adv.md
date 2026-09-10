# Go generics advanced (example)

- Type sets (`~int | ~string`) constrain underlying kinds flexibly.
- Comparability flows through `comparable` constraint automatically.
- Generic methods remain unsupported; hoist to package-level functions.
- `any` slices need type switches before operations resume.
- Zero values (`var zero T`) initialize generic accumulators safely.
- Constraints as interfaces document requirements readably.
- Monomorphization duplicates code per instantiation (binary cost).
- Benchmark generic versus concrete hot paths before assuming parity.
- Stdlib generics (`slices`, `maps`, `cmp`) cover 90 percent of needs.
- Reflection (`reflect`) still handles truly dynamic leftovers.
