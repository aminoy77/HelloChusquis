# Go basics

- In Go, every program starts at `package main` with `func main()`; other packages are importable libraries.
- In Go, `gofmt` (or `go fmt`) standardizes formatting; run it before committing, and `go vet` catches common mistakes.
- In Go, `x := 10` declares with type inference while `var x int` declares explicitly; `:=` works only inside functions.
- In Go, unused variables and imports are compile errors; remove them or assign to `_`.
- In Go, slices are views: `s := []int{1, 2, 3}`, `append(s, 4)` may reallocate, so always keep the result.
- In Go, `make([]int, length, capacity)` preallocates; maps need `make(map[string]int)` before writing.
- In Go, maps return the zero value for missing keys; use `v, ok := m[k]` to distinguish absence.
- In Go, functions return errors as values: `result, err := f()` followed by `if err != nil` handling.
- In Go, `defer f.Close()` schedules cleanup at function return; deferred calls run LIFO.
- In Go, `for` is the only loop: `for i := 0; ...`, `for cond`, `for range`, and bare `for` for infinite loops.
- In Go, `for i, v := range slice` iterates index and copy; take `&slice[i]` when mutation is needed.
- In Go, structs group fields (`type User struct { Name string }`); exported names start uppercase.
- In Go, methods attach via receivers: `func (u User) Name() string`; pointer receivers mutate the original.
- In Go, interfaces are satisfied implicitly: any type implementing the methods qualifies, no declaration needed.
- In Go, the empty interface `any` holds any value; recover the type with a type assertion or type switch.
- In Go, `go.mod` pins the module path and dependency versions; `go mod tidy` reconciles requirements.
- In Go, `go test ./...` runs all package tests; table-driven tests with `t.Run` subtests are idiomatic.
- In Go, exported identifiers need doc comments starting with the name for `golint`-style tooling.
