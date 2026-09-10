# C functions and scope

- In C, declare prototypes in headers so callers compile before seeing definitions.
- In C, `static` functions hide helpers inside one translation unit.
- In C, pass large structs by `const` pointer to avoid whole-value copies.
- In C, return heap or static results, never addresses of local variables.
- In C, `void f(void)` declares truly zero parameters; bare `void f()` is legacy style.
- In C, recursion depth is bounded by stack size; convert deep loops to iteration.
- In C, `inline` hints header-defined small functions to avoid call overhead.
- In C, variadic `...` with `va_list` implements printf-style APIs carefully.
- In C, `const` on pointer parameters documents read-only intent to callers.
- In C, one definition per function program-wide; headers carry only declarations.
