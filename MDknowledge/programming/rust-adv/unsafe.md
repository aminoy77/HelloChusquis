# Rust unsafe (example)

- `unsafe` blocks suspend checks; safety invariants become the author's proof burden.
- Raw pointers (`*const/*mut`) dereference only inside unsafe blocks.
- FFI declarations (`extern "C"`) bridge C ABIs with manual contract care.
- `MaybeUninit` defers initialization without undefined behavior.
- Union field reads are unsafe; writes stay safe operations.
- `unsafe impl Send/Sync` asserts thread safety the compiler cannot verify.
- Miri interprets programs catching undefined behavior experimentally.
- Encapsulate unsafety in safe abstractions (Vec, Mutex) as the ecosystem norm.
- Audit `unsafe` per crate before security-sensitive dependencies.
- Soundness holes (past `Pin`, lifetime bugs) get CVEs and rapid fixes.
