# C++ exceptions

- In C++, `throw std::runtime_error("msg")` signals failures with descriptive types.
- In C++, catch by `const` reference (`catch (const std::exception& e)`) to avoid slicing.
- In C++, RAII destructors run during stack unwinding, releasing resources automatically.
- In C++, destructors must not throw; mark them `noexcept` to prevent `terminate`.
- In C++, `noexcept` on move operations unlocks standard-container optimizations.
- In C++, constructor failures throw since constructors return nothing to check.
- In C++, catch specific types before `catch (...)`, which swallows everything blindly.
- In C++, `std::optional<T>` and `std::expected` (C++23) express recoverable absence without throws.
- In C++, exception guarantees rank basic (no leaks) above strong (rollback) above nothrow.
- In C++, `-fno-exceptions` codebases use error codes instead; match surrounding style.
