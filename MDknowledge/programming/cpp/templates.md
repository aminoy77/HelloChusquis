# C++ templates

- In C++, `template <typename T> T max(T a, T b)` stamps functions per argument type.
- In C++, class templates like `template <typename T> class Box {...}` parameterize containers.
- In C++, definitions must be visible at instantiation, so templates live in headers.
- In C++, `typename` and `class` are interchangeable in template parameter lists.
- In C++, non-type params (`template <int N>`) bake constants like array sizes into types.
- In C++, specialization tailors implementations for specific types like `bool` vectors.
- In C++, variadic `template <typename... Args>` folds arbitrary argument packs.
- In C++, C++20 concepts (`requires`) constrain templates with readable error messages.
- In C++, `if constexpr` selects branches at compile time per instantiated type.
- In C++, template errors surface at instantiation sites; read the first error line, not the last.
