# Go error handling

- In Go, `if err != nil { return err }` after calls is the central error idiom.
- In Go, `fmt.Errorf("load %s: %w", name, err)` wraps with `%w` preserving the chain.
- In Go, `errors.Is` matches wrapped sentinels and `errors.As` extracts typed errors.
- In Go, sentinel `var ErrNotFound = errors.New(...)` values enable caller comparisons.
- In Go, custom error types implement `Error() string` on value or pointer receivers consistently.
- In Go, `panic` is for unrecoverable bugs, not routine failures; libraries should return errors.
- In Go, `recover()` in deferred functions converts panics at controlled boundaries only.
- In Go, `defer` runs LIFO, so stack cleanup calls in reverse acquisition order.
- In Go, named returns plus bare `return` suit long functions; short ones prefer explicit values.
- In Go, log errors with context once, at the handling layer, not at every wrap point.
