# C++ smart pointers

- In C++, RAII ties resource lifetime to object lifetime: acquisition in the constructor, release in the destructor.
- In C++, `std::unique_ptr<T>` owns exclusively and cannot be copied, only moved with `std::move`.
- In C++, create unique owners with `auto p = std::make_unique<T>(args...)` instead of raw `new`.
- In C++, `std::shared_ptr<T>` shares ownership via reference counting; the object dies with the last owner.
- In C++, create shared owners with `std::make_shared<T>(args...)`, which allocates object and control block together.
- In C++, `std::weak_ptr<T>` observes without owning; call `.lock()` to get a temporary `shared_ptr` before use.
- In C++, parent-to-child `shared_ptr` plus child-to-parent `weak_ptr` breaks reference cycles that would otherwise leak.
- In C++, pass `const T&` for read-only access and `T&` for mutation; smart pointers are for ownership transfer, not every parameter.
- In C++, return `std::unique_ptr<T>` from factories to express single ownership transfer clearly.
- In C++, never build two smart pointers from the same raw pointer; the double control block causes double deletion.
- In C++, `unique_ptr<T[]>` manages dynamic arrays with `p[i]` indexing; prefer `std::vector` unless ownership semantics demand it.
- In C++, custom deleters (`unique_ptr<FILE, decltype(&fclose)>`) adapt smart pointers to C resources like files and handles.
- In C++, `std::move` casts to rvalue but moves nothing itself; the move constructor/assignment does the work.
- In C++, moved-from standard objects stay valid but unspecified; only safe operations are destruction and reassignment.
- In C++, enable `shared_from_this` when an object must hand out `shared_ptr` to itself safely.
- In C++, cyclic `shared_ptr` graphs never reach zero count; audit ownership diagrams for back-edges.
- In C++, prefer stack objects and standard containers first; reach for smart pointers at genuine ownership boundaries.
- In C++, `-fsanitize=address` catches use-after-free and leaks even in smart-pointer code during development.
