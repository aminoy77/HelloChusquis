# Rust structs and enums

- In Rust, `struct Point { x: f64, y: f64 }` groups fields with `impl` blocks for methods.
- In Rust, tuple structs `struct Meters(f64);` add type safety to bare numbers.
- In Rust, enums carry data: `enum E { Ok(u32), Err(String) }` replaces tagged unions.
- In Rust, `match` on enums must be exhaustive or include a `_` fallback arm.
- In Rust, methods take `self`, `&self`, or `&mut self` by ownership need.
- In Rust, associated functions like `String::new()` omit `self` and act as constructors.
- In Rust, `#[derive(Debug, Clone)]` auto-implements inspection and duplication.
- In Rust, field init shorthand `Point { x, y }` uses same-named variables directly.
- In Rust, `..Default::default()` fills remaining struct fields from defaults.
- In Rust, `struct` update syntax `..other` moves non-Copy fields out of the source.
