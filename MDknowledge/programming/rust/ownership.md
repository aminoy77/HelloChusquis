# Rust ownership

- In Rust, each value has exactly one owner, and the value is dropped when the owner goes out of scope.
- In Rust, assigning a `String` moves ownership; the source binding becomes unusable afterwards.
- In Rust, `Copy` types like integers and bools duplicate on assignment instead of moving.
- In Rust, `.clone()` makes an explicit deep copy when a move would invalidate needed data.
- In Rust, borrowing with `&` creates shared references: many readers allowed, no writers.
- In Rust, `&mut` creates exactly one mutable reference with no other active references to the same value.
- In Rust, references must never outlive their referent; the compiler rejects dangling borrows.
- In Rust, function signatures encode intent: `fn f(s: String)` takes ownership, `fn f(s: &str)` only borrows.
- In Rust, prefer borrowing (`&str`, `&[T]`, `&T`) in parameters and return owned values from constructors.
- In Rust, the borrow checker forbids mutation while borrowed views exist; restructure to shorten borrow spans.
- In Rust, slices `&s[0..2]` borrow part of a collection with bounds checked at runtime.
- In Rust, lifetimes (`<'a>`) name how long references stay valid; elision covers the common single-input cases.
- In Rust, structs holding references need lifetime parameters, e.g. `struct View<'a> { text: &'a str }`.
- In Rust, `Rc<T>` enables multiple ownership on one thread and `Arc<T>` extends it across threads.
- In Rust, `RefCell<T>` moves borrow checks to runtime for single-threaded interior mutability.
- In Rust, `Mutex<T>` and `RwLock<T>` guard shared data between threads; lock poison signals a panicked holder.
- In Rust, splitting borrows (e.g. disjoint struct fields) satisfies the checker without cloning.
- In Rust, NLL (non-lexical lifetimes) ends borrows at last use, so reusing a variable afterwards often just works.
