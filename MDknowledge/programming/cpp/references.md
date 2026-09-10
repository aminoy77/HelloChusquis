# C++ references and const

- In C++, `int& r = x` aliases without null or reseat; references must bind at creation.
- In C++, `const int&` parameters borrow cheaply and accept temporaries safely.
- In C++, return references only to outliving objects, never to locals.
- In C++, `const` member functions promise no mutation and work on const instances.
- In C++, `constexpr` evaluates at compile time when inputs are constant expressions.
- In C++, `const_cast` removing constness to mutate is undefined for truly-const objects.
- In C++, rvalue references (`T&&`) bind temporaries to power move semantics.
- In C++, `std::move` enables moves but the constructor performs them.
- In C++, perfect forwarding (`T&&` + `std::forward`) preserves value categories through wrappers.
- In C++, prefer values for small trivial types and const-references for heavy ones.
