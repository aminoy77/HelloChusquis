# Go modules

- In Go, `go mod init example.com/app` starts versioned modules at the repository root.
- In Go, `go.mod` records the module path plus required dependency versions.
- In Go, `go get example.com/pkg@v1.2.3` adds precise dependency versions.
- In Go, `go mod tidy` adds missing and drops unused requirements automatically.
- In Go, `go mod vendor` snapshots dependencies for offline or hermetic builds.
- In Go, semantic import versioning (`/v2` suffixes) marks breaking major releases.
- In Go, `go.sum` checksums lock dependency content against tampering.
- In Go, `replace` directives redirect modules to local paths during development.
- In Go, `go list -m all` audits the full resolved dependency graph.
- In Go, minimal version selection picks the highest required version across the graph.
