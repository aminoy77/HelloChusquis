# Rust error handling

- In Rust, `Result<T, E>` forces handling success and failure as values, not exceptions.
- In Rust, `?` early-returns errors with automatic `From` conversion up the chain.
- In Rust, `Option<T>` models absence; `unwrap` panics, so prefer combinators in libraries.
- In Rust, `.map`, `.and_then`, `.unwrap_or`, and `.ok_or` transform without nesting matches.
- In Rust, `thiserror` derives library error enums while `anyhow` simplifies application errors.
- In Rust, `expect("context")` documents invariants better than bare `unwrap`.
- In Rust, `Result::map_err` translates low-level errors at module boundaries.
- In Rust, `#[must_use]` warns when callers ignore meaningful return values.
- In Rust, panics unwind by default; `panic = 'abort'` suits tiny binaries.
- In Rust, `catch_unwind` isolates panics at FFI or plugin boundaries only.
