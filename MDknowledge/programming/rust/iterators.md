# Rust iterators

- In Rust, `.iter()` borrows, `.iter_mut()` mutably borrows, and `.into_iter()` consumes collections.
- In Rust, `map`, `filter`, and `collect::<Vec<_>>()` transform lazily until collected.
- In Rust, `filter_map` fuses filtering plus unwrapping `Option` results in one pass.
- In Rust, `fold(init, f)` aggregates while `reduce` omits the seed for non-empty iterators.
- In Rust, `.enumerate()` pairs indices and `.zip()` walks two iterators in lockstep.
- In Rust, `.take(n)`/`.skip(n)` bound infinite or oversized sequences cheaply.
- In Rust, `.any()`/`.all()` short-circuit predicates without full traversal.
- In Rust, `.find()` returns the first match as `Option`; `.position()` returns its index.
- In Rust, `.chain()` concatenates and `.flat_map()` maps plus flattens nested iterators.
- In Rust, `.collect()` also builds `String`, `HashMap`, and `Result<Vec,_>, E>` targets.
