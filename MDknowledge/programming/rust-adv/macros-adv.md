# Rust macros advanced (example)

- Derive macros read ASTs via `syn` and emit code via `quote`.
- Attribute macros (`#[route]`) transform annotated items wholesale.
- Function-like macros (`sql!`) embed DSLs with custom syntax.
- `macro_rules!` fragment specifiers (`:expr`, `:ty`) constrain matcher shapes.
- Hygiene keeps macro locals from colliding with call-site names.
- `cargo expand` reveals generated code when debugging derives.
- Declarative macros compose poorly across crate boundaries; re-export helpers.
- Compile times suffer under heavy derive stacks — profile builds.
- `build.rs` codegen complements macros for file-driven generation.
- Template engines (Askama, Tera) often beat macro-heavy HTML DSLs.
