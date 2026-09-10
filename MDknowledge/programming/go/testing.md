# Go testing

- In Go, `func TestAdd(t *testing.T)` in `*_test.go` files runs under `go test`.
- In Go, table tests (slice of input/want structs plus `t.Run`) scale cases without duplication.
- In Go, `t.Fatal` stops the test while `t.Error` records and continues through cases.
- In Go, `t.Helper()` marks helpers so failures point at callers, not utilities.
- In Go, `t.TempDir()` provides auto-cleaned scratch directories per test.
- In Go, `go test -run TestName` filters and `-v` streams subtest results.
- In Go, `go test -race` detects data races and should gate concurrent packages.
- In Go, `go test -cover` reports statement coverage to find untested branches.
- In Go, benchmarks `func BenchmarkX(b *testing.B)` loop over `b.N` under `go test -bench=.`.
- In Go, `testdata/` directories hold fixtures ignored by the build tool.
