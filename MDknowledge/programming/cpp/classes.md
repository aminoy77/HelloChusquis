# C++ classes

- In C++, `class` members are private by default while `struct` members are public by default.
- In C++, constructors run at creation; prefer member-initializer lists (`C(int x) : x(x) {}`) over body assignment.
- In C++, the destructor `~C()` releases resources; it runs automatically for stack objects.
- In C++, mark single-argument constructors `explicit` to block unintended implicit conversions.
- In C++, `const` member functions promise not to mutate state and can be called on const objects.
- In C++, `virtual` enables overriding; a base class meant for polymorphism needs a virtual destructor.
- In C++, `override` on derived methods makes signature mismatches a compile error instead of silent hiding.
- In C++, pure virtual `virtual void f() = 0;` makes a class abstract; derived classes must implement it.
- In C++, the rule of three/five: a class managing a resource needs destructor, copy/move constructor, and copy/move assignment.
- In C++, `= default` requests compiler-generated special members and `= delete` forbids operations like copying.
- In C++, `friend` grants selected functions or classes access to private members for operators and tests.
- In C++, `static` members are shared by all instances; `static` member functions lack `this`.
- In C++, `public`/`protected`/`private` inheritance controls how base members appear to users of the derived class.
- In C++, prefer composition over deep inheritance hierarchies for flexible designs.
- In C++, `struct` with public data plus free functions suits plain records; `class` suits invariants.
- In C++, initialize members in declaration order, not initializer-list order, to avoid warnings and bugs.
- In C++, `noexcept` on move operations and destructors enables standard-library optimizations.
- In C++, slicing copies only the base part when assigning a derived object to a base value; use pointers/references polymorphically.
