# Rust basics

- In Rust, `cargo new app` scaffolds a project and `cargo run` builds plus executes it.
- In Rust, bindings are immutable by default; `let mut x = 1;` opts into mutation.
- In Rust, `cargo build --release` produces optimized binaries; plain `cargo build` is a fast debug build.
- In Rust, `cargo test` runs unit tests and `cargo fmt` plus `cargo clippy` enforce style and lints.
- In Rust, `match` must be exhaustive: cover every enum variant or add a `_` fallback arm.
- In Rust, `Option<T>` (`Some`/`None`) replaces null; `Result<T, E>` (`Ok`/`Err`) replaces exceptions.
- In Rust, the `?` operator propagates errors early from functions returning `Result` or `Option`.
- In Rust, `String` owns growable text while `&str` borrows a string slice; `&s` and `s.to_string()` convert between them.
- In Rust, `println!` with `{}` formats `Display` types and `{:?}` uses `Debug` for developer output.
- In Rust, vectors use `vec![1, 2, 3]`, `v.push(x)`, and `v[i]` (panics out of range) versus `v.get(i)` returning `Option`.
- In Rust, `HashMap` lives in `std::collections` and needs explicit import to use.
- In Rust, `if let Some(x) = opt` and `while let` patterns handle single cases without full `match`.
- In Rust, integer overflow panics in debug builds but wraps in release; use explicit `wrapping_*`/`checked_*` where it matters.
- In Rust, `const MAX: u32 = 100;` is a compile-time constant while `static` has a fixed memory address.
- In Rust, crates are managed in `Cargo.toml`; `cargo update` refreshes versions within the declared constraints.
- In Rust, `#[derive(Debug, Clone, PartialEq)]` auto-implements common traits on structs and enums.
- In Rust, `todo!()` and `unimplemented!()` mark unfinished code paths that panic with a message when hit.
- In Rust, documentation tests in `///` comments compile and run under `cargo test`, keeping examples honest.
