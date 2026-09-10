# C preprocessor

- In C, `#include <stdio.h>` searches system paths while `#include "util.h"` searches the current project first.
- In C, `#define MAX 100` creates a manifest constant; prefer `enum` or `const` for typed, debuggable values.
- In C, parenthesize macro bodies and parameters: `#define SQUARE(x) ((x) * (x))` avoids precedence surprises.
- In C, macro arguments evaluate every time they appear, so `SQUARE(i++)` increments twice — use inline functions instead.
- In C, `static inline` functions in headers beat function-like macros for type safety and single evaluation.
- In C, multi-statement macros wrap in `do { ... } while (0)` so they behave like one statement in `if/else`.
- In C, `#ifdef DEBUG` / `#ifndef` / `#endif` compile code conditionally on defined symbols.
- In C, header include guards (`#ifndef UTIL_H` / `#define UTIL_H` / ... / `#endif`) prevent double-definition errors.
- In C, `#pragma once` is a widely supported shorter alternative to manual include guards.
- In C, predefined macros `__FILE__`, `__LINE__`, `__func__`, and `__DATE__` aid logging and diagnostics.
- In C, `#error "message"` stops compilation with a custom message when configuration assumptions break.
- In C, stringizing `#x` turns a macro argument into a string literal and `a##b` pastes tokens together.
- In C, `#if` expressions must be compile-time constant; use them for version and platform selection.
- In C, `#include` order (own header, then project, then system) surfaces missing dependencies early.
- In C, never `#include` a `.c` file; share code through headers plus exactly one definition.
- In C, `-DNAME=value` on the compiler command line defines macros without editing source.
