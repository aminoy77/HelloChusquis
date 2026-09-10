# Rust error patterns (example)

- `thiserror` derives Display/From for library error enums ergonomically.
- `anyhow::Result` plus context chains suit application codebases.
- `?` converts via `From` automatically across error boundaries.
- `map_err` translates low-level errors at module edges deliberately.
- `expect` documents invariants; `unwrap` admits review scrutiny.
- `Result::ok` discards errors explicitly where truly ignorable.
- `NonZeroU32` and friends encode invariants in types preventing errors.
- `#[must_use]` warns when callers ignore meaningful returns.
- `panic = abort` suits tiny binaries skipping unwinding tables.
- `eyre` customizes anyhow reports with installable hooks.
